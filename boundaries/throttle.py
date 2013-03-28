"""
Virtually all of this code is from
http://github.com/tomchristie/django-rest-framework

Thanks!
"""
import logging
import time

from django.core.cache import cache

from boundaries.models import app_settings

logger = logging.getLogger(__name__)

class BaseThrottle(object):
    """
    Rate throttling of requests.
    """
    def allow_request(self, request, view):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError('.allow_request() must be overridden')

    def wait(self):
        """
        Optionally, return a recommended number of seconds to wait before
        the next request.
        """
        return None

class SimpleRateThrottle(BaseThrottle):
    """
    A simple cache implementation, that only requires `.get_cache_key()`
    to be overridden.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute
    on the :class:`.View` class.  The attribute is a tuple of
    (number of requests, number of seconds) -- that is, (60, 60)
    means to throttle after 60 requests in a minute.

    Previous request information used for throttling is stored in the cache.
    """

    timer = time.time
    settings = app_settings
    cache_format = 'throtte_%(scope)s_%(ident)s'
    scope = None

    def __init__(self):
        if not getattr(self, 'rate', None):
            self.rate = self.get_rate()
        self.num_requests, self.duration = self.rate

    def get_cache_key(self, request, view):
        """
        Should return a unique cache-key which can be used for throttling.
        Must be overridden.

        May return `None` if the request should not be throttled.
        """
        raise NotImplementedError('.get_cache_key() must be overridden')

    def get_rate(self):
        """
        Get the allowed request rate from settings.
        """
        if not getattr(self, 'scope', None):
            msg = ("You must set either `.scope` or `.rate` for '%s' throttle" %
                   self.__class__.__name__)
            raise Exception(msg)

        try:
            return self.settings.DEFAULT_THROTTLE_RATES[self.scope]
        except KeyError:
            msg = "No default throttle rate set for '%s' scope" % self.scope
            raise Exception(msg)

    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        self.history = cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure(request, view)
        return self.throttle_success(request, view)

    def throttle_success(self, request, view):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self, request, view):
        """
        Called when a request to the API has failed due to throttling.
        """
        if self.settings.THROTTLE_LOG:
            logger.warning("Request throttled.",
                extra={'request': request})
        return False

    def wait(self):
        """
        Returns the recommended next request time in seconds.
        """
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1

        return remaining_duration / float(available_requests)

class AnonRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by a anonymous users.

    The IP address of the request will be used as the unique cache key.
    """
    scope = 'anon'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.ident
        }

    def allow_request(self, request, view):
        """Determine whether this is a whitelisted request."""
        if app_settings.THROTTLE_APIKEY_LIST:
            key = request.META.get(app_settings.THROTTLE_APIKEY_HEADER.upper().replace('-', '_'))
            if not key:
                key = request.GET.get(app_settings.THROTTLE_APIKEY_PARAM)
            if key and key in app_settings.THROTTLE_APIKEY_LIST:
                return True

        self.ident = request.META.get(
            self.settings.THROTTLE_IP_HEADER, None)
        if self.ident in app_settings.THROTTLE_IP_WHITELIST:
            return True

        # Not whitelisted; continue checking by IP
        return super(AnonRateThrottle, self).allow_request(request, view)

    def throttle_failure(self, request, view):
        if self.ident == '127.0.0.1':
            logger.warning("Throttling localhost. Is %s inaccurate because of proxies?"
                % self.settings.THROTTLE_IP_HEADER)
        return super(AnonRateThrottle, self).throttle_failure(request, view)
