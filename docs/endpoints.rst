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

*****
Login
*****

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

************
Backup codes
************

* ``/mfa/codes/regenerate/`` ``[POST]``
    | Requests new batch of backup codes.
    | Payload:

        * ``method`` MFA method name

********
Settings
********

* ``/mfa/config/`` ``[GET]``
    | Display app's configuration

* ``/mfa/user-active-methods/`` ``[GET]``
    | Display methods activated by user

* ``/mfa/change-primary-method/`` ``[POST]``
    | Change default authentication method
    | Payload:

        * ``method`` MFA method name
        * ``code`` auth code received by specified channel
