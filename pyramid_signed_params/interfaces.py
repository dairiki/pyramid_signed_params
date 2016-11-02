# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from zope.interface import Interface


class ISignedParamsService(Interface):
    def sign_query(params, max_age=None, kid=None):
        """Sign request parameters

        ``Params`` should be an iterable of pairs, or a object with an
        ``.items()`` method which will return an iterable of pairs.
        Both members of each pair should be (or be coercable to) text
        strings.

        Returns an iterable of pairs of text strings.

        ``Max_age``, if specified should be an integer or
        a ``timedelta`` instance specifying how long the signature will
        remain valid, or ``None`` if the signature should not expire.

        """

    def signed_params(params):
        """Extract signed parameters from a request.

        ``Params`` should be an iterable of pairs of text strings, or
        a object with an ``.items()`` method which will return an
        iterable of pairs of text strings.

        Returns a MultiDict containing all parameters found with a valid
        signature.

        """


class IJWTSecretProvider(Interface):
    def valid_secrets(kid=None):
        """Get a list of valid secrets for kid
        """

    def signing_secret(kid=None):
        """Get signing key for kid"""
