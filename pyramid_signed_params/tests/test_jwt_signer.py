# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime, timedelta
from itertools import product
import logging
import re

import jwt
from pyramid.exceptions import ConfigurationError
import pytest
from webob.multidict import MultiDict

from pyramid_signed_params.interfaces import IJWTSecretProvider
from pyramid_signed_params.jwt_signer import (
    UnrecognizedKID,
    JWTSecretProvider,
    JWTSignedParamsService,
    JWTSecretProviderFactory,
    _to_text,
    _getall,
    )


@pytest.fixture
def params():
    return {'foo': 'bar'}


@pytest.fixture
def secrets():
    return b'secret', b'oldsecret'


@pytest.fixture
def caplog_debug(caplog):
    caplog.set_level(logging.DEBUG)
    return caplog


class TestJWTSecretProviderFactory(object):
    @pytest.fixture
    def secret_provider(self, request_, secrets):
        return JWTSecretProvider(request_, secrets)

    def test_init_no_secrets(self, request_):
        secrets = []
        with pytest.raises(ValueError):
            JWTSecretProvider(request_, secrets)

    def test_valid_secrets(self, secret_provider, secrets):
        assert secret_provider.valid_secrets() == secrets

    def test_valid_secrets_change_with_csrf(self, secret_provider, request_):
        secrets = secret_provider.valid_secrets()
        assert len(secrets) > 0

        csrf_secrets = secret_provider.valid_secrets(kid='csrf')
        assert len(csrf_secrets) == len(secrets)
        assert all(s1 != s2 for s1, s2 in product(csrf_secrets, secrets))

        request_.session.new_csrf_token()
        new_csrf_secrets = secret_provider.valid_secrets(kid='csrf')
        assert len(new_csrf_secrets) == len(secrets)
        assert all(s1 != s2
                   for s1, s2 in product(new_csrf_secrets, csrf_secrets))

    def test_valid_secrets_bad_kid(self, secret_provider):
        with pytest.raises(UnrecognizedKID):
            secret_provider.valid_secrets(kid='foo')

    def test_signing_secret(self, secret_provider, secrets):
        assert secret_provider.signing_secret() == secrets[0]
        assert secret_provider.signing_secret(kid='csrf') != secrets[0]

    def test_signing_secret_changes_with_csrf(self, secret_provider):
        secret = secret_provider.signing_secret()
        assert secret_provider.signing_secret(kid='csrf') != secret

    def test_signing_secret_bad_kid(self, secret_provider):
        with pytest.raises(UnrecognizedKID):
            secret_provider.signing_secret(kid='foo')

    def test_from_settings(context, request_):
        settings = {
            'pyramid_signed_params.secret': '  foo\n\n bar\n\n',
            }
        factory = JWTSecretProviderFactory.from_settings(settings)
        secret_provider = factory(context, request_)
        assert secret_provider.valid_secrets() == (b'foo', b'bar')

    @pytest.mark.parametrize('secrets', [
        '   \n\t\n',
        None,
        ])
    def test_from_settings_no_secrets(self, secrets):
        settings = {}
        if secrets:
            settings['pyramid_signed_params.secret'] = secrets
        with pytest.raises(ConfigurationError):
            JWTSecretProviderFactory.from_settings(settings)


@pytest.mark.usefixtures('caplog_debug')
class TestJWTSignedParamsService(object):
    @pytest.fixture
    def signing_secret(self, secrets):
        return secrets[0]

    @pytest.fixture(autouse=True)
    def secret_provider(self, config, secrets, signing_secret):
        provider = DummySecretProvider(secrets, signing_secret)
        config.register_service(provider, IJWTSecretProvider)
        return provider

    @pytest.fixture
    def service(self, context, request_):
        return JWTSignedParamsService(context, request_)

    @pytest.mark.parametrize('kid', [None, 'csrf'])
    @pytest.mark.parametrize('max_age', [None, 30])
    @pytest.mark.parametrize('params', [
        [],
        {'a': u'böø'},
        [('foo', 'bar'), ('foo', 'baz')],
        ])
    @pytest.mark.parametrize('signing_secret', [
        b'secret',
        b'oldsecret',
        ])
    def test_round_trip(self, service, params, kid, max_age):
        signed = service.sign_query(params, kid=kid, max_age=max_age)
        verified = service.signed_params(signed)
        assert verified == MultiDict(params)

    @pytest.mark.parametrize('signing_secret', ['badsecret'])
    def test_badsecret(self, service, params, caplog):
        signed = service.sign_query(params)
        verified = service.signed_params(signed)
        assert len(verified) == 0
        assert 'Signature verification failed' in caplog.text

    def test_expired(self, service, params, caplog):
        a_minute_ago = datetime.utcnow() - timedelta(60)
        service._utcnow = lambda: a_minute_ago
        signed = service.sign_query(params,  max_age=30)
        verified = service.signed_params(signed)
        assert not verified
        assert 'expired' in caplog.text

    def test_signed_params_ignores_garbage(self, service, caplog):
        signed = {'_sp': 'garbage'}
        verified = service.signed_params(signed)
        assert len(verified) == 0
        assert 'Invalid JWT token' in caplog.text

    @pytest.mark.parametrize('signing_secret', [b'secret'])
    @pytest.mark.parametrize('secrets', [(b'ssh-rsa',)])
    def test_signed_params_invalid_key(self, service, caplog):
        signed = service.sign_query({})
        verified = service.signed_params(signed)
        assert len(verified) == 0
        assert 'Invalid JWT token' in caplog.text

    def test_signed_params_invalid_alg(self, service, caplog, monkeypatch):
        # Test coverage for the ``except InvalidTokenError``
        # clause in JWTSignedParamsService._verify().
        token = jwt.encode({'_qs': {}}, 'secret', headers={'alg': 'HS256'})
        monkeypatch.setattr(service, 'accepted_algorithms', ('HS384'))
        verified = service.signed_params({'_sp': token})
        assert len(verified) == 0
        assert any(
            re.search(r'Alg(orithm)?.*not (allowed|supported)',
                      logrec.getMessage(),
                      re.I)
            for logrec in caplog.records
            )


@pytest.mark.usefixtures('caplog_debug')
class TestJWTSignedParamsServiceIntegration(object):
    @pytest.fixture(autouse=True)
    def secret_provider(self, config, request_, secrets):
        provider = JWTSecretProvider(request_, secrets)
        config.register_service(provider, IJWTSecretProvider)
        return provider

    @pytest.fixture
    def service(self, context, request_):
        return JWTSignedParamsService(context, request_)

    def test_new_csrf_invalidates_signature(self, service, params, request_):
        signed = service.sign_query(params, kid='csrf')
        request_.session.new_csrf_token()
        verified = service.signed_params(signed)
        assert len(verified) == 0

    def test_signed_params_invalid_kid(self, service, caplog):
        token = jwt.encode({}, 'secret', headers={'kid': 'bugger'})
        verified = service.signed_params({'_sp': token})
        assert len(verified) == 0
        assert 'Unrecognized kid ' in caplog.text


@pytest.mark.parametrize('obj, expected', [
    (u'Fü', u'Fü'),
    ('Fu', u'Fu'),
    (42, u'42'),
    ])
def test_to_text(obj, expected):
    assert _to_text(obj) == expected


items = [
    ('k', 'v1'),
    ('x', 'v2'),
    ('k', 'v3')
    ]


@pytest.mark.parametrize('params, expected', [
    (items, ['v1', 'v3']),
    (MultiDict(items), ['v1', 'v3']),
    (dict(items), ['v3']),
    ({}, []),
    ])
def test_getall(params, expected):
    assert _getall(params, 'k') == expected


class DummySecretProvider(object):
    def __init__(self, secrets, signing_secret=None):
        if signing_secret is None:
            signing_secret = secrets[0]  # if len(secrets) > 0 else None
        self.secrets = secrets
        self._signing_secret = signing_secret

    def valid_secrets(self, kid=None):
        return self.secrets

    def signing_secret(self, kid=None):
        return self._signing_secret
