======================
Pyramid Signed Params
======================

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

*******
Authors
*******

`Jeff Dairiki`_

.. _Jeff Dairiki: mailto:dairiki@dairiki.org
