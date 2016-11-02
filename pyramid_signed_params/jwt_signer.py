# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from collections import Mapping
from datetime import datetime, timedelta
import logging
import sys

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidKeyError,
    InvalidTokenError,
    )
from pyramid.compat import binary_type, bytes_, reraise, text_, text_type
from pyramid.settings import aslist
from webob.multidict import MultiDict
from zope.interface import implementer

from .interfaces import IJWTSecretProvider, ISignedParamsService


log = logging.getLogger(__name__)


class UnrecognizedKID(Exception):
    """An unrecognized ``kid`` was encountered in a JWT token
    """


def includeme(config):
    settings = config.get_settings()
    config.register_service_factory(
        JWTSecretProviderFactory.from_settings(settings),
        IJWTSecretProvider)
    config.register_service_factory(
        JWTSignedParamsService,
        ISignedParamsService)


@implementer(IJWTSecretProvider)
class JWTSecretProvider(object):
    def __init__(self, request, secrets):
        if len(secrets) == 0:
            raise ValueError("No secrets?")
        self.request = request
        self.secrets = tuple(map(bytes_, secrets))

    def valid_secrets(self, kid=None):
        secrets = self.secrets
        if kid is None:
            return secrets
        elif kid == 'csrf':
            session = self.request.session
            extra = bytes_(session.get_csrf_token())
            return tuple(secret + extra for secret in secrets)
        else:
            raise UnrecognizedKID("Unrecognized kid %r" % kid)

    def signing_secret(self, kid=None):
        return self.valid_secrets(kid)[0]


class JWTSecretProviderFactory(object):
    def __init__(self, secrets):
        self.secrets = tuple(map(bytes_, secrets))

    def __call__(self, context, request):
        return JWTSecretProvider(request, self.secrets)

    @classmethod
    def from_settings(cls, settings, prefix='pyramid_signed_params.'):
        name = prefix + 'secrets'
        secrets = aslist(settings.get(name, ''), flatten=False)
        if len(secrets) > 0:
            return cls(secrets)
        else:
            log.warn("No secret(s) configured, please set %s in your settings",
                     name)
            return None


@implementer(ISignedParamsService)
class JWTSignedParamsService(object):
    algorithm = 'HS256'
    _utcnow = staticmethod(datetime.utcnow)  # testing

    def __init__(self, context, request):
        self.secret_provider = request.find_service(IJWTSecretProvider)

    def sign_query(self, params, max_age=None, kid=None):
        if hasattr(params, 'items'):
            params = params.items()
        params = [(_to_text(key), _to_text(value)) for key, value in params]

        headers = {}
        secret = self.secret_provider.signing_secret(kid)
        if kid is not None:
            headers['kid'] = kid
        claims = {'_qs': params}
        if max_age is not None:
            if not isinstance(max_age, timedelta):
                max_age = timedelta(seconds=max_age)
            claims['exp'] = self._utcnow() + max_age

        token = jwt.encode(claims, secret,
                           algorithm=self.algorithm,
                           headers=headers)
        return (('_sp', text_(token)),)

    def signed_params(self, params):
        tokens = _getall(params, '_sp')
        data = []
        for token in tokens:
            try:
                claims = self._verify(token)
            except ExpiredSignatureError as ex:
                # FIXME: way to indicate that an expired token was encountered
                log.info("Expired JWT token: %s", ex)
            except (InvalidTokenError, InvalidKeyError, UnrecognizedKID) as ex:
                log.debug("Invalid JWT token: %s", ex)
            else:
                data.extend(claims['_qs'])
        return MultiDict(data)

    def _verify(self, token):
        kid = jwt.get_unverified_header(token).get('kid')
        secrets = self.secret_provider.valid_secrets(kid)
        assert len(secrets) > 0
        exc_info = None
        have_decode_error = False
        for secret in secrets:
            try:
                return jwt.decode(token, secret)
            except ExpiredSignatureError:
                # Signature expired. No point trying other secrets.
                raise
            except DecodeError:
                # One reason for a DecodeError is signature
                # verification failure. Keep trying with remaining
                # secrets, but remember the first exception.
                #
                # Note that if we encounter both DecodeErrors and
                # InvalidKeyErrors, we'd rather report the
                # DecodeError.
                if not have_decode_error:
                    exc_info = sys.exc_info()
                    have_decode_error = True
            except InvalidKeyError:
                # InvalidKeyError is secret-specific as well.
                if exc_info is None:
                    exc_info = sys.exc_info()
            except InvalidTokenError:
                # Any other problems are presumably not going to get
                # better retrying with another secret.  Quit now.
                raise
        # reraise saved exception
        reraise(*exc_info)


def _to_text(obj):
    """ Coerce value to (unicode) text.

    """
    if not isinstance(obj, text_type):
        if isinstance(obj, binary_type):
            obj = obj.decode('ascii', 'strict')
        else:
            obj = text_type(obj)
    return obj


def _getall(params, name):
    if hasattr(params, 'getall'):
        return params.getall(name)
    elif isinstance(params, Mapping):
        return [params[name]] if name in params else []
    else:
        return [v for k, v in params if k == name]
