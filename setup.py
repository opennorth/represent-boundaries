from setuptools import setup

setup(
    name = "represent-boundaries",
    version = "0.1",
    url='http://github.com/rhymeswithcycle/represent-boundaries',
    description="A Web API to geographical districts loaded from shapefiles. Packaged as a Django app.",
    license = "MIT",
    packages = [
        'boundaries',
        'boundaries.management',
        'boundaries.management.commands'
    ],
    install_requires = [
        'django-jsonfield>=0.7.1',
        'django-appconf',
    ],
    classifiers = [
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django',
        'Topic :: Scientific/Engineering :: GIS',
    ]
)
