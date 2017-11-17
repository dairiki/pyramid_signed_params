# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from webob.multidict import MultiDict

from .interfaces import ISignedParamsService


def includeme(config):
    config.include('pyramid_services')
    config.add_request_method(signed_params, reify=True)
    config.add_request_method(sign_query)

    settings = config.get_settings()
    if 'pyramid_signed_params.secret' in settings:
        config.include('pyramid_signed_params.jwt_signer')


def signed_params(request):
    """ Get a multidict containing all valid signed parameters found.

    """
    signer = request.find_service(ISignedParamsService)
    try:
        params = request.params
    except UnicodeDecodeError:
        # If the HTTP request had improperly encoded data, there are
        # no valid signed params.
        return MultiDict()
    else:
        return signer.signed_params(params)


def sign_query(request, params, max_age=None, kid=None):
    """ Sign parameters

    Example usage::

        query = {'return_url': 'http://example.com/dont-mess-with-this'}
        url = request.route_url('myroute', _query=request.sign_query(query))

    """
    signer = request.find_service(ISignedParamsService)
    return signer.sign_query(params, max_age=max_age, kid=kid)
