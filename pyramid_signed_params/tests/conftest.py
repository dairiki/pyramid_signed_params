# -*- coding: utf-8 -*-
from __future__ import absolute_import

import random
from string import hexdigits

from pyramid.request import Request, apply_request_extensions
from pyramid import testing

import pytest


@pytest.fixture
def config():
    config = testing.setUp()
    config.set_session_factory(lambda request: DummySession())
    config.include('pyramid_services')
    yield config
    testing.tearDown()


@pytest.fixture
def context():
    return testing.DummyResource()


@pytest.fixture
def request_(config):
    request = Request.blank('/')
    request.registry = config.registry
    apply_request_extensions(request)
    return request


class DummySession(dict):
    def new_csrf_token(self):
        token = ''.join(random.choice(hexdigits) for _ in range(32))
        self['_csrft_'] = token
        return token

    def get_csrf_token(self):
        token = self.get('_csrft_')
        if token is None:
            return self.new_csrf_token()
        return token
