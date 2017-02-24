from setuptools import setup

setup(
    name="represent-boundaries",
    version="0.9.1",
    description="A web API to geographic boundaries loaded from shapefiles, packaged as a Django app.",
    author="Open North Inc.",
    author_email="represent@opennorth.ca",
    url="http://represent.poplus.org/",
    license="MIT",
    # If packaged as a zip/egg, Django will by default not find static files.
    zip_safe=False,
    # Tells setuptools to look in MANIFEST.in
    include_package_data=True,
    packages=[
        'boundaries',
        'boundaries.management',
        'boundaries.management.commands',
        'boundaries.migrations',
    ],
    install_requires=[
        'django-appconf',
    ],
    extras_require={
        'test': 'testfixtures',
    },
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
