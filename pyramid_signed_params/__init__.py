# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

import warnings

from .interfaces import ISignedParamsService


def includeme(config):
    config.include('pyramid_services')
    config.add_request_method(signed_params, reify=True)
    config.add_request_method(sign_query)

    settings = config.get_settings()
    if 'pyramid_signed_params.secret' in settings:
        config.include('pyramid_signed_params.jwt_signer')
    try:
        config.find_service_factory(ISignedParamsService)
    except ValueError:
        warnings.warn(
            "No service has been configured ISignedParamsService. "
            "The request methods added by pyramid_signed_params will not "
            "work without one. (Consider setting "
            "pyramid_signed_params.secret in your .ini file.)")


def signed_params(request):
    """ Get a multidict of any valid signed parameters
    """
    signer = request.find_service(ISignedParamsService)
    return signer.signed_params(request.params)


def sign_query(request, params, max_age=None, kid=None):
    """ Sign parameters

    Example usage::

        query = {'return_url': 'http://example.com/dont-mess-with-this'}
        url = request.route_url('myroute', _query=request.sign_query(query))

    """
    signer = request.find_service(ISignedParamsService)
    return signer.sign_query(params, max_age=max_age, kid=kid)
