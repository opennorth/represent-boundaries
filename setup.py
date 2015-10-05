from setuptools import setup

setup(
    name="represent-boundaries",
    version="0.7.4",
    description="A web API to geographic boundaries loaded from shapefiles, packaged as a Django app.",
    author="Open North Inc.",
    author_email="represent@opennorth.ca",
    url="http://represent.poplus.org/",
    license="MIT",
    packages=[
        'boundaries',
        'boundaries.management',
        'boundaries.management.commands',
        'boundaries.migrations',
    ],
    install_requires=[
        'jsonfield>=0.9.20,<1',
        'django-appconf',
    ],
    extras_require={
        'test': 'testfixtures',
    },
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
