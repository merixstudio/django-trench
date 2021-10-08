Settings
========

Defaults and customization
**************************

| You can customize settings by adding ``TRENCH_AUTH`` dict in your ``settings.py``:

.. code-block:: python

    TRENCH_AUTH = {
        "USER_MFA_MODEL": "trench.MFAMethod",
        "USER_ACTIVE_FIELD": "is_active",
        "BACKUP_CODES_QUANTITY": 5,
        "BACKUP_CODES_LENGTH": 12,
        "BACKUP_CODES_CHARACTERS": (string.ascii_letters + string.digits),
        "SECRET_KEY_LENGTH": 32,
        "DEFAULT_VALIDITY_PERIOD": 30,
        "CONFIRM_DISABLE_WITH_CODE": False,
        "CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE": True,
        "ALLOW_BACKUP_CODES_REGENERATION": True,
        "ENCRYPT_BACKUP_CODES": True,
        "APPLICATION_ISSUER_NAME": "MyApplication",
        "MFA_METHODS": {
            "email": {
                "VERBOSE_NAME": _("email"),
                "VALIDITY_PERIOD": 60 * 10,
                "HANDLER": "trench.backends.basic_mail.SendMailMessageDispatcher",
                "SOURCE_FIELD": "email",
                "EMAIL_SUBJECT": _("Your verification code"),
                "EMAIL_PLAIN_TEMPLATE": "trench/backends/email/code.txt",
                "EMAIL_HTML_TEMPLATE": "trench/backends/email/code.html",
            },
            # Your other backends here
        }
    }

Properties
**********

.. list-table::
    :header-rows: 1

    * - Property
      - Description
      - Type
      - Default value
    * - ``USER_MFA_MODEL``
      - You can specify your own model for storing MFA data. For compatibility reasons it is recommended to inherit from the ``trench.MFAMethod`` model when extending.
      - ``str``
      - ``trench.MFAMethod``
    * - ``USER_ACTIVE_FIELD``
      - Field on ``User`` model which stores information whether user's account is active or not.
      - ``str``
      - ``is_active``
    * - ``BACKUP_CODES_QUANTITY``
      - Number of backup codes to be generated.
      - ``int``
      - ``5``
    * - ``BACKUP_CODES_LENGTH``
      - Number of characters that the backup code should consist of.
      - ``int``
      - ``12``
    * - ``BACKUP_CODES_CHARACTERS``
      - Characters that should be used to generate backup codes.
      - ``str``
      - ``string.ascii_letters + string.digits``
    * - ``ENCRYPT_BACKUP_CODES``
      - Defines whether backup codes should be encrypted before storing them into the database.
      - ``bool``
      - ``True``
    * - ``SECRET_KEY_LENGTH``
      - Length of the shared secret key.

        *Note: secrets must be at least 160 bits.*
      - ``int``
      - ``32``
    * - ``DEFAULT_VALIDITY_PERIOD``
      - Period when OTP code validates positively (in seconds). Becomes a default if no validity period has been declared on a specific authentication method.
      - ``int``
      - ``30``
    * - ``CONFIRM_DISABLE_WITH_CODE``
      - When set to ``True`` requires a code verification to disable given authentication method.
      - ``bool``
      - ``False``
    * - ``CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE``
      - When set to ``True`` requires a code verification to regenerate backup code.
      - ``bool``
      - ``True``
    * - ``ALLOW_BACKUP_CODES_REGENERATION``
      - When set to ``True`` regeneration of backup codes is enabled.
      - ``bool``
      - ``True``
    * - ``APPLICATION_ISSUER_NAME``
      - Issuer name for the QR code generator.
      - ``str``
      - ``MyApplication``
    * - ``MFA_METHODS``
      - A dictionary which holds all authentication methods and its settings. New method can be added as a next item.
      - ``dict``
      - Described in `backends`_ section.

Method item properties
**********************

| You can add as much custom properties to each of your backends as you like, but be sure to include the ones mentioned below as they are required to make your backend compatible with Trench mechanism.

.. list-table::
    :header-rows: 1

    * - Property
      - Description
      - Type
    * - ``VERBOSE_NAME``
      - Full name of the method.
      - ``str``
    * - ``VALIDITY_PERIOD``
      - OTP code validity (in seconds).
      - ``int``
    * - ``HANDLER``
      - String path pointing to the location of your backend class definition.
      - ``str``

.. _backends: https://django-trench.readthedocs.io/en/latest/backends.html
