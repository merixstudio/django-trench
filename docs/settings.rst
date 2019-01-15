Additional settings
===================

| You can customize settings by adding ``TRENCH_AUTH`` dict in your ``settings.py``:

.. code-block:: python

    TRENCH_AUTH = {
        'FROM_EMAIL': 'your@email.com',
        'USER_ACTIVE_FIELD': 'is_active',
        'BACKUP_CODES_QUANTITY': 5,
        'BACKUP_CODES_LENGTH': 10,  # keep (quantity * length) under 200
        'BACKUP_CODES_CHARACTERS': (
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ),
        'ENCRYPT_BACKUP_CODES': True,
        'DEFAULT_VALIDITY_PERIOD': 30,
        'CONFIRM_DISABLE_WITH_CODE': False,
        'CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE': True,
        'ALLOW_BACKUP_CODES_REGENERATION': True,
        'APPLICATION_ISSUER_NAME': 'MyApplication',
        'MFA_METHODS': {
            'email': {
                'VERBOSE_NAME': _('email'),
                'VALIDITY_PERIOD': 60 * 10,
                'FIELD': 'email',
                'HANDLER': 'trench.backends.basic_mail.SendMailBackend',
                'SERIALIZER': 'trench.serializers.RequestMFACreateEmailSerializer',
                'SOURCE_FIELD': 'email',
            },
            ...,
        },
    }

FROM_EMAIL
""""""""""
Email address to be used as sender's while using email backend for sending codes.

USER_ACTIVE_FIELD
"""""""""""""""""
Field on ``User`` model which stores information whether user's account is active or not.
Default: ``is_active``

BACKUP_CODES_QUANTITY
"""""""""""""""""""""
Number of backup codes to be generated.

BACKUP_CODES_LENGTH
"""""""""""""""""""
Length of backup code.

BACKUP_CODES_CHARACTERS
"""""""""""""""""""""""
Range of characters to be used in backup code.

ENCRYPT_BACKUP_CODES
""""""""""""""""""""
Backup codes to be encrypted before saving.
Default: ``True``

DEFAULT_VALIDITY_PERIOD
"""""""""""""""""""""""
Period when OTP code validates positively (in seconds). Becomes a default if no validity period has been declared on a specific authentication method.

CONFIRM_DISABLE_WITH_CODE
"""""""""""""""""""""""""
If ``True`` requires a code verification to disable a current authentication method.
Default: ``False``

CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE
"""""""""""""""""""""""""""""""""""""""""""
If ``True`` requires a code verification to regenerate backup code.

ALLOW_BACKUP_CODES_REGENERATION
"""""""""""""""""""""""""""""""
If ``True`` allows regenerate backup codes.
Default: ``True``


APPLICATION_ISSUER_NAME
"""""""""""""""""""""""
Issuer name for QR generation.

MFA_METHODS
"""""""""""
A dictionary which holds all authentication methods and its settings. New method can be added as a next item.

Method item properties
**********************
* ``'VERBOSE_NAME'`` method name
* ``'VALIDITY_PERIOD'`` OTP code validity
* ``'HANDLER'`` location of the method's handler
* ``'SERIALIZER'`` location of a serializer
* ``'SOURCE_FIELD'`` field on a User model utilised in the method (i.e. field storing phone number for SMS)
