# -*- coding: utf-8 -*-
from __future__ import absolute_import

from pyramid import testing
import pytest
from six import text_type
from webob.multidict import MultiDict

from pyramid_signed_params.interfaces import ISignedParamsService
from pyramid_signed_params import includeme, signed_params, sign_query


@pytest.fixture
def signed_params_service(config):
    service = DummySignedParamsService()
    config.register_service(service, ISignedParamsService)
    return service


@pytest.fixture
def params():
    return {'foo': 'bar'}


class Test_includeme(object):
    # This is a basic functional test of the whole system.
    @pytest.fixture
    def settings(self):
        return {'pyramid_signed_params.secret': 'sekret'}

    @pytest.fixture
    def config(self, settings):
        config = testing.setUp(settings=settings)
        includeme(config)
        yield config
        testing.tearDown()

    def test(self, config, request_, params):
        signed = request_.sign_query(params)
        request_.GET.extend(signed)
        assert request_.signed_params == params


def test_signed_params(request_, params, signed_params_service):
    request_.GET.extend(signed_params_service.sign_query(params))
    assert signed_params(request_) == params


@pytest.fixture
def misencoded_request(request_):
    request_.environ['QUERY_STRING'] = '\xb5'
    with pytest.raises(UnicodeDecodeError):
        request_.params
    return request_


@pytest.mark.usefixtures('signed_params_service')
def test_signed_params_ignores_decode_errors(misencoded_request):
    assert signed_params(misencoded_request) == {}


def test_sign_query(request_, params, signed_params_service):
    signed = sign_query(request_, params)
    signed_params_service.signed_params(signed) == params


class DummySignedParamsService(object):
    def __init__(self, prefix='_signed_'):
        self.prefix = prefix

    def sign_query(self, params, max_age=None, kid=None):
        prefix = self.prefix
        if hasattr(params, 'items'):
            params = params.items()
        signed = [(u'%s%s' % (prefix, k), text_type(v)) for k, v in params]
        if max_age is not None:
            signed.append((u'max_age', text_type(max_age)))
        if kid is not None:
            signed.append((u'kid', kid))
        return signed

    def signed_params(self, params):
        prefix = self.prefix
        if hasattr(params, 'items'):
            params = params.items()
        return MultiDict((k[len(prefix):], v)
                         for k, v in params
                         if k.startswith(prefix))
