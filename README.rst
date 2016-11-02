#####################################################
Cryptographically Signed Query Parameters for Pyramid
#####################################################

|version| |py_versions| |license| |build status|

***********
Description
***********

This package provides a method for pyramid_ applications to sign parameters
which are passed in query strings (or POST bodies).

The initial motivation for this was to be able to pass a ``return_url``
to a views without turning the app into open redirector.

Other use cases include being able to generate URLs (e.g. to be included in
emails) which can be used to bypass the normal authentication/authorization
mechanisms.

.. _pyramid: https://trypyramid.com/

*******************
Basic Usage Example
*******************

Construct a URL which could be e-mailed out to allow changing the
password of a given user::

    # Construct a URL with some signed parameters
    params = {'userid': 'fred', 'action': 'change-pw'}
    signed_params = request.sign_query(params, max_age=3600)
    url = request.route_url('change-pw', _query=signed_params)

Then, in the change-pw view::

    if request.signed_params['action'] != 'change-pw':
        raise HTTPForbidden()
    userid = request.signed_params['userid']

    # Do whatever needs to be done to change the given users password

Note that because we passed ``max_age=3600`` to ``sign_query``, the
URL will only work for an hour.


*******
Authors
*******

`Jeff Dairiki`_

.. _Jeff Dairiki: mailto:dairiki@dairiki.org


.. ==== Badges ====

.. |build status| image::
    https://travis-ci.org/dairiki/pyramid_signed_params.svg?branch=master
    :target: https://travis-ci.org/dairiki/pyramid_signed_params

.. |downloads| image::
    https://img.shields.io/pypi/dm/pyramid_signed_params.svg
    :target: https://pypi.python.org/pypi/pyramid_signed_params/
    :alt: Downloads
.. |version| image::
    https://img.shields.io/pypi/v/pyramid_signed_params.svg
    :target: https://pypi.python.org/pypi/pyramid_signed_params/
    :alt: Latest Version
.. |py_versions| image::
    https://img.shields.io/pypi/pyversions/pyramid_signed_params.svg
    :target: https://pypi.python.org/pypi/pyramid_signed_params/
    :alt: Supported Python versions
.. |py_implementation| image::
    https://img.shields.io/pypi/implementation/pyramid_signed_params.svg
    :target: https://pypi.python.org/pypi/pyramid_signed_params/
    :alt: Supported Python versions
.. |license| image::
    https://img.shields.io/pypi/l/pyramid_signed_params.svg
    :target: https://github.com/dairiki/pyramid_signed_params/blob/master/LICENSE.txt
    :alt: License
.. |dev_status| image::
    https://img.shields.io/pypi/status/pyramid_signed_params.svg
    :target: https://pypi.python.org/pypi/pyramid_signed_params/
    :alt: Development Status
