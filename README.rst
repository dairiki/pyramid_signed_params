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

************
Installation
************

``Pyramid-signed-params`` can be installed from PyPI_ using ``pip`` or
``easy_install`` (or ``buildout``.)  You should probably be installing it in a virtual
environment.

.. _PyPI: https://pypi.python.org/pypi/pyramid-signed-params

*************
Configuration
*************

You must configure at least one signing secret in your app settings.
The secret should be a random, unguessable string.  E.g. in your app’s
``.ini`` file::

  pyramid_signed_params.secret = RGWO7nZ6W6AiPIUcXQN2iahJIThwH9BbpyZ7Lc1XfaOkPGt1GY

.. hint::

  You can specify multiple signing keys (one per line.)  If
  you do, the first key will be used for signing, while all keys will
  be tried when verifying signatures.  This can be useful when rolling
  out a new signing key.

Activate the package by including it in your pyramid application.

.. code-block:: python

  config.include('pyramid-signed-params')

This will add two new attributes to pyramid’s ``request``.

- ``request.sign_query(query, max_age=None, kid=None)``

  Used to sign query arguments, e.g.

  .. code-block:: python

    # Pass the current URL as a signed *return_url* parameter to another view
    query = {'return_url': request.url}
    other_url = request.route_url('other', _query=request.sign_query(query))

  The ``max_age`` parameter can be used to generate signatures which expire after a certain
  amount of time.

  Passing ``kid="csrf"`` will create signatures which will be
  invalidated whenever the session’s CSRF token is changed.

- ``request.signed_params``

  This *reified* property will contain a multidict populated with all
  parameters passed to the request which were signed with a valid
  signature.

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
Caution
*******

This package provides no inherent protection against replay attacks.
If an attacker has access to a set of signed parameters, he may pass
those signed parameters, unmodified, to any URL within the app (or
other apps sharing the same signing secret.)

*******
Authors
*******

`Jeff Dairiki`_

.. _Jeff Dairiki: mailto:dairiki@dairiki.org


.. ==== Badges ====

.. |build status| image::
    https://github.com/dairiki/pyramid_signed_params/actions/workflows/tests.yml/badge.svg?branch=master
    :target: https://github.com/dairiki/pyramid_signed_params/actions/workflows/tests.yml

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
