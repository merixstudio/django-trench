#############
API Endpoints
#############

*********************
MFA method activation
*********************

| Request a new method activation and get an authentication code by specified channel.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /:method_name/activate/``
      -
    * - Parameters
      - ``:method_name`` - **required**
      - Allowed method names: ``email``, ``app``, ``yubi``, ``sms_api``, ``sms_twilio``
    * - Payload
      - ``empty``
      -
    * - Successful response
      - .. code-block:: json

            {
                "details": "Email message with MFA code has been sent."
            }

      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "error": "Requested MFA method does not exist."
            }

      - **HTTP status:**

        ``400 BAD REQUEST``

**********************************
MFA method activation confirmation
**********************************

| Accepts the authentication code, activates the method and returns backup codes if successful.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /:method_name/activate/confirm/``
      -
    * - Parameters
      - ``:method_name`` - **required**
      - Allowed method names: ``email``, ``app``, ``yubi``, ``sms_api``, ``sms_twilio``
    * - Payload
      - .. code-block:: json

            {
                "code": "123456"
            }

      - ``code`` - authentication code received by specified method
    * - Successful response
      - .. code-block:: json

            {
                "backup_codes": [
                    "111111",
                    "222222",
                    "333333",
                    "444444",
                    "555555",
                    "666666",
                ]
            }

      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "error": "MFA method already active."
            }

      - **HTTP status:**

        ``400 BAD REQUEST``

***********************
MFA method deactivation
***********************

| Deactivates the specified method. Depeding on :doc:`settings` sends out an authentication code and requires confirmation.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /:method_name/deactivate/``
      -
    * - Parameters
      - ``:method_name`` - **required**
      - Allowed method names: ``email``, ``app``, ``yubi``, ``sms_api``, ``sms_twilio``
    * - Payload
      - .. code-block:: json

            {
                "code": "123456"
            }

      - ``code`` - authentication code received by specified method
    * - Successful response
      - ``empty``
      - **HTTP status:**

        ``204 NO CONTENT``
    * - Error response
      - .. code-block:: json

            {
                "error": "Requested MFA method does not exist."
            }

      - **HTTP status:**

        ``400 BAD REQUEST``

*************
Send the code
*************

| Triggers sending out a code. If no ``method`` specified in the payload user's primary MFA method will be used.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /code/request/``
      -
    * - Payload
      - .. code-block:: json

            {
                "method": "email"
            }

      - ``method`` **(optional)** - one of: ``email``, ``app``, ``yubi``, ``sms_api``, ``sms_twilio``
    * - Successful response
      - ``empty``
      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "details": "Email message with MFA code has been sent."
            }

      - **HTTP status:**

        ``400 BAD REQUEST``

********************************
Login - first step (JWT example)
********************************

| If MFA is enabled for a given user returns ``ephemeral_token`` required in next step as well as current auth ``method``.
| Otherwise returns ``access`` and ``refresh`` tokens.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /login/``
      -
    * - Payload
      - .. code-block:: json

            {
                "username": "Merixstudio",
                "password": "SecretPassword123#"
            }

      -
    * - Successful response (MFA enabled)
      - .. code-block:: json

            {
                "ephemeral_token": "1-qrx0ph-e76b858094f0321525b42ad7141b5720816b6a4c",
                "method": "email"
            }

      - **HTTP status:**

        ``200 OK``
    * - Successful response (MFA disabled)
      - .. code-block:: json

            {
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI...AhJA",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI...T_t8"
            }

      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "details": "Unable to login with provided credentials."
            }

      - **HTTP status:**

        ``401 UNAUTHENTICATED``

********************************
Login - second step (JWT example)
********************************

| Requires ``ephemeral_token`` generated in previous step and OTP code.
| Returns ``access`` and ``refresh`` tokens after successful authentication.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /login/code/``
      -
    * - Payload
      - .. code-block:: json

            {
                "ephemeral_token": "1-qrx0ph-e76b858094f0321525b42ad7141b5720816b6a4c",
                "code": "925738"
            }

      -
    * - Successful response
      - .. code-block:: json

            {
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI...AhJA",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI...T_t8"
            }

      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "details": "Unable to login with provided credentials."
            }

      - **HTTP status:**

        ``401 UNAUTHENTICATED``

*************************
Generate new backup codes
*************************

| If you've set the ``CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE`` option to ``True`` in the :doc:`settings` then passing the ``code`` in request payload is required.

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``POST /:method_name/codes/regenerate/``
      -
    * - Parameters
      - ``:method_name`` - **required**
      - Allowed method names: ``email``, ``app``, ``yubi``, ``sms_api``, ``sms_twilio``
    * - Payload
      - .. code-block:: json

            {
                "code": "123456"
            }

      - ``code`` - authentication code received by specified method
    * - Successful response
      - .. code-block:: json

            {
                "backup_codes": [
                    "111111",
                    "222222",
                    "333333",
                    "444444",
                    "555555",
                    "666666",
                ]
            }

      - **HTTP status:**

        ``200 OK``
    * - Error response
      - .. code-block:: json

            {
                "error": "Requested MFA method does not exist."
            }

      - **HTTP status:**

        ``400 BAD REQUEST``

*****************
Get configuration
*****************

| Returns MFA configuration

.. list-table:: API endpoint specification
    :stub-columns: 1

    * - Request
      - ``GET /mfa/config/``
      -
    * - Successful response
      - .. code-block:: json

            {
                "methods": [
                    "sms_twilio",
                    "sms_api",
                    "email",
                    "app",
                    "yubi"
                ],
                "confirm_disable_with_code": true,
                "confirm_regeneration_with_code": true,
                "allow_backup_codes_regeneration": true
            }

      - **HTTP status:**

        ``200 OK``

* ``/mfa/user-active-methods/`` ``[GET]``
    | Display methods activated by user

* ``/mfa/change-primary-method/`` ``[POST]``
    | Change default authentication method
    | Payload:

        * ``method`` MFA method name
        * ``code`` auth code received by specified channel
