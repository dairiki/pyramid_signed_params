# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages

VERSION = '0.1b5'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

install_requires = [
    'pyjwt >= 1.3',
    'pyramid',
    'pyramid_services',
    ]

tests_require = [
    'pytest >= 3.3',            # 3.3 required for catchlog
    ]

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
setup_requires = ['pytest-runner'] if needs_pytest else []

setup(
    name='pyramid-signed-params',
    version=VERSION,
    description='Cryptographically signed query parameters for pyramid',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        ("Topic :: Internet :: WWW/HTTP :: Dynamic Content"
         " :: CGI Tools/Libraries"),
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        ],
    author='Jeff Dairiki',
    author_email='dairiki@dairiki.org',
    license='BSD',
    url="https://github.com/dairiki/pyramid_signed_params",
    keywords='web pyramid cryptography query_string',

    packages=find_packages(),


    include_package_data=True,
    zip_safe=False,

    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        },
    )
