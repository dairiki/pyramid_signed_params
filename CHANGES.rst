*******
Changes
*******

Release 0.1a4 (2016-11-02)
==========================

- The setting for configuring the JWT signing secret(s) has been
  renamed to ``pyramid_signed_param.secret`` from
  ``pyramid_signed_param.secrets``.  Basic usage involve only a single
  secret. (Two allow for rotation of secrets, any configured secrets are
  accepted when verifying signatures, but only the first is used for
  creating new signatures.)

- ``Pyramid_signed_params.include`` now issues a warning if the
  ``ISignedParamsService`` is not configured.

- ``JWTSecretProviderFactory`` now raises a ``ConfigurationError``
  if no secrets are found in the app ``settings``.


Release 0.1a3 (2016-11-02)
==========================

Initial release.
