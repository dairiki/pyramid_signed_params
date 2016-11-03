*******
Changes
*******

Release 0.1a4 (Unreleased)
==========================

- ``Pyramid_signed_params.include`` now issues a warning if the
  ``ISignedParamsService`` is not configured.

- ``JWTSecretProviderFactory`` now raises a ``ConfigurationError``
  if no secrets are found in the app ``settings``.


Release 0.1a3 (2016-11-02)
==========================

Initial release.
