import logging
from collections.abc import Mapping
from datetime import datetime, timedelta

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    )
from pyramid.exceptions import ConfigurationError
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
class JWTSecretProvider:
    def __init__(self, request, secrets):
        if len(secrets) == 0:
            raise ValueError("No secrets?")
        self.request = request
        self.secrets = tuple(
            sec if isinstance(sec, bytes) else sec.encode("latin-1")
            for sec in secrets
        )

    def valid_secrets(self, kid=None):
        secrets = self.secrets
        if kid is None:
            return secrets
        elif kid == 'csrf':
            session = self.request.session
            extra = session.get_csrf_token().encode("latin-1")
            return tuple(secret + extra for secret in secrets)
        else:
            raise UnrecognizedKID("Unrecognized kid %r" % kid)

    def signing_secret(self, kid=None):
        return self.valid_secrets(kid)[0]


class JWTSecretProviderFactory:
    def __init__(self, secrets):
        self.secrets = tuple(
            sec if isinstance(sec, bytes) else sec.encode("latin-1")
            for sec in secrets
        )

    def __call__(self, context, request):
        return JWTSecretProvider(request, self.secrets)

    @classmethod
    def from_settings(cls, settings, prefix='pyramid_signed_params.'):
        name = prefix + 'secret'
        secrets = aslist(settings.get(name, ''), flatten=False)
        if len(secrets) > 0:
            return cls(secrets)
        else:
            raise ConfigurationError(
                "No secret(s) configured, please set %s in your settings"
                % name)


@implementer(ISignedParamsService)
class JWTSignedParamsService:
    algorithm = 'HS256'
    accepted_algorithms = ('HS256', 'HS384', 'HS512')

    _utcnow = staticmethod(datetime.utcnow)  # testing

    def __init__(self, context, request):
        self.secret_provider = request.find_service(IJWTSecretProvider)

    def sign_query(self, params, max_age=None, kid=None):
        """Sign query parameters

        ``Params`` should be an iterable of two-tuples, or an object which
        has an ``.items()`` method which returns a sequence of two-tuples.
        The elements of the two-tuples should be text strings (or coercible
        to text strings.)

        Returns a sequence of two-tuples, suitable for passing to
        ``urlencode`` (or similar) to generate a query string (or POST
        body.)

        ``Max_age``, if specified should be an integer or a ``timedelta``
        instance specifying how long the signature will be good for.
        If ``max_age`` is not specified or is ``None``, the signature will
        not expire.

        ``Kid`` should either be ``None`` or a text string.  It is passed
        to the service registered ``IJWTSecretProvider`` to retrieve the
        signing secret(s).  If the default secret provider is used, setting
        ``kid`` to ``"csrf"`` will result in signatures which are only
        valid for the current session.  (The signatures will be invalidated
        with the CSRF token changes.)

        Note that multiple set of parameters can be signed with different
        parameters::

            query = []
            query.extend(request.sign_params({'long': 'time'}))
            query.extend(request.sign_params({'temp': 'hot'}, max_age=60))
            url = request.route_url('myroute', _query=query)

        When the signed parameters are verified, the parameters from all
        valid tokens will be merged.

        """
        if hasattr(params, 'items'):
            params = params.items()
        params = [(str(key), str(value)) for key, value in params]

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
        if not isinstance(token, str):
            token = token.decode("latin-1")  # pyjwt 1.x
        return (('_sp', token),)

    def signed_params(self, params):
        """Get signed parameters.

        ``Params`` should be an iterable of two-tuples or text
        strings, or an object which has an ``.items()`` method which
        returns such a sequence of two-tuples.

        Returns a multidict containing all parameters found in
        ``params`` which have valid signatures.  Unrecognized parameters
        found in ``params``, or those with invalid signatures will be ignored.

        """
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
        saved_exc = None
        have_invalid_signature_error = False
        for secret in secrets:
            try:
                return jwt.decode(token, secret,
                                  algorithms=self.accepted_algorithms)
            except ExpiredSignatureError:
                # Signature expired. No point trying other secrets.
                raise
            except InvalidSignatureError as exc:
                # Note that with PyJWT < 1.6, this is actually a DecodeError.
                # Note that if we encounter both DecodeErrors and
                # InvalidKeyErrors, we'd rather report the
                # DecodeError.
                if not have_invalid_signature_error:
                    saved_exc = exc
                    have_invalid_signature_error = True
            except InvalidKeyError as exc:
                # InvalidKeyError is secret-specific as well.
                if saved_exc is None:
                    saved_exc = exc
            except (InvalidTokenError, DecodeError):
                # Any other problems are presumably not going to get
                # better retrying with another secret.  Quit now.
                raise
        raise saved_exc


def _getall(params, name):
    if hasattr(params, 'getall'):
        return params.getall(name)
    elif isinstance(params, Mapping):
        return [params[name]] if name in params else []
    else:
        return [v for k, v in params if k == name]
