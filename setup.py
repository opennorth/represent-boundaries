from setuptools import setup

setup(
    name = "represent-boundaries",
    version = "0.3",
    description="A web API to geographic boundaries loaded from shapefiles, packaged as a Django app.",
    author="Open North Inc.",
    author_email="represent@opennorth.ca",
    url="http://represent.poplus.org/",
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
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django',
        'Topic :: Scientific/Engineering :: GIS',
    ]
)
