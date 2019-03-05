=========
Changelog
=========


0.2.1 (2019-03-05)
==================

* Added setting for secret_key_length and set it to default of 16
* Replace split method on ephemeral_token with rsplit
* Add AllowAny to the mixins for login views
* Changed _backup_codes to TextField


0.2.0 (2019-01-15)
==================

* Added auth backend for YubiKey
* Changed default email backend to Django's built-in
* Added sms auth backend for smsapi.pl
* Added support for Simple JWT
* Added encryption for backup codes with customisation setting
* Updated translations
* Added Transifex for translations
* Added flake8 and isort to tox tests
* Changed default settings to more verbose
* Fixed setup to install only trench package
* Fixed pytest import mistmatch error when running test in Docker


0.1.0 (2018-11-08)
==================

* Initial release
