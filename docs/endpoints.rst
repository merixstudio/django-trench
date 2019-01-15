API Endpoints
=============

MFA method activation
"""""""""""""""""""""

* ``/[method name]/activate/`` ``[POST]``
    | Request a new method activation and get an authentication code by specified channel.
    | Payload:

        * ``method`` MFA method name

* ``/[method name]/activate/confirm/``` ``[POST]``
    | Accepts the auth code, activates the method and returns backup codes
    | Payload:

        * ``code`` auth code received by specified channel

* ``/[method name]/deactivate/``` ``[POST]``
    | Deactivates the specified method. Depeding on :doc:`settings` sends out a auth code and requires confirmation.
    | Payload:

        * ``code`` auth code received by specified channel

``[method_name]`` one of MFA methods specified in your project ``settings.py``. Check out :doc:`settings`.

* ``/code/request/`` ``[POST]``
    | Triggers sending out a code.

Login
"""""
* ``/login/`` ``[POST]``
    | First step, if 2FA is enable returns ``ephemeral_token`` required in next step as well as current auth ``method``, otherwise logs in user.
    | Payload:
        * ``username``
        * ``password``

* ``/login/code/`` ``[POST]``
    | Requires token generated in previous step and OTP code, logs in user (returns ``token``)
    | Payload:
        * ``ephemeral_token``
        * ``code``

Backup codes
""""""""""""
* ``/mfa/codes/regenerate/`` ``[POST]``
    | Requests new batch of backup codes.
    | Payload:

        * ``method`` MFA method name

Settings
""""""""
* ``/mfa/config/`` ``[GET]``
    | Display app's configuration

* ``/mfa/user-active-methods/`` ``[GET]``
    | Display methods activated by user

* ``/mfa/change-primary-method/`` ``[POST]``
    | Change default authentication method
    | Payload:

        * ``method`` MFA method name
        * ``code`` auth code received by specified channel
