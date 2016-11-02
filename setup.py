# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

VERSION = '0.1a3'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'pyjwt',
    'pyramid',
    'pyramid_services',
    ]

testing_extras = [
    'pytest >= 3.0',            # 3.0 required for pytest.approx
    'pytest-catchlog',
    ]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

cmdclass = {'test': PyTest}

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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        ],
    author='Jeff Dairiki',
    author_email='dairiki@dairiki.org',
    license='BSD',
    url="https://pypi.python.org/pypi/pyramid-signed-params",
    keywords='web pyramid cryptography query_string',

    packages=find_packages(),

    install_requires=requires,

    include_package_data=True,
    zip_safe=False,

    tests_require=testing_extras,
    cmdclass=cmdclass,
    extras_require={
        "testing": testing_extras,
        },
    )
