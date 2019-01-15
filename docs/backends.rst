Authentication backends
=======================

| ``django-trench`` comes with three predefined authentication methods.
| Custom backends can be easily added by inheritating ``AbstractMessageDispatcher`` class.

Built-in backends
"""""""""""""""""
Email
*****
| This basic method utilise build-in Django backend. You'll need to have Email Backend setup. Check out `Django documentation`_.

Text/SMS
********
| SMS backends sends out text messages with `Twilio`_ or `Smsapi.pl`_. Credentials can be set in method's specific settings.

.. code-block:: python

    TRENCH_AUTH = {
        (...)
        'MFA_METHODS': {
            'sms_twilio': {
                'VERBOSE_NAME': 'sms',
                'VALIDITY_PERIOD': 60 * 10,
                'HANDLER': 'trench.backends.twilio.TwilioBackend',
                'SOURCE_FIELD': 'phone_number',
                'TWILIO_ACCOUNT_SID': TWILIO SID,
                'TWILIO_AUTH_TOKEN': TWILIO TOKEN,
                'TWILIO_VERIFIED_FROM_NUMBER': TWILIO REGISTERED NUMBER,
            },
            ...,
        },
    }

Read more in :doc:`settings`.

Authentication apps
*******************
| This backend returns OTP based QR link to be scanned by apps like Gooogle Authenticator and Authy.

.. code-block:: python

    TRENCH_AUTH = {
        (...)
        'MFA_METHODS': {
            'app': {
                'VERBOSE_NAME': 'app',
                'VALIDITY_PERIOD': 60 * 10,
                'USES_THIRD_PARTY_CLIENT': True,
                'HANDLER': 'trench.backends.application.ApplicationBackend',
            },
            ...,
        },
    }

YubiKey
*******

.. code-block:: python

    TRENCH_AUTH = {
        (...)
        'MFA_METHODS': {
            'yubi': {
                'VERBOSE_NAME': 'yubi',
                'HANDLER': 'trench.backends.yubikey.YubiKeyBackend',
                'SOURCE_FIELD': 'yubikey_id',
                'YUBICLOUD_CLIENT_ID': '',
            }
            ...,
        },
    }

Adding own authentication method
""""""""""""""""""""""""""""""""
| Base on provided examples you can create own handler class, which heritates from ``AbstractMessageDispatcher``.

.. code-block:: python

    from trench.backends import AbstractMessageDispatcher


    class CustomAuthBackend(AbstractMessageDispatcher):

        def dispatch_message(self, *args, **kwargs):
            (....)
            return {'data': 'ok'}

| It may be also required to provide a custom serializer depending on what information need to be passed on from user.
| In order to run your own method update settings as follows:

.. code-block:: python

    TRENCH_AUTH = {
        (...)
        'MFA_METHODS': {
            'yourmethod': {
                'VERBOSE_NAME': 'yourmethod',
                'VALIDITY_PERIOD': 60 * 10,
                'SOURCE_FIELD': 'phone_number', # if your backend requires custom field on User model
                'HANDLER': 'yourapp.backends.CustomAuthBackend',
                'SERIALIZER': 'yourapp.serializers.CustomAuthSerializer',
            },
            ...,
        },
    }


.. _`Django documentation`: https://docs.djangoproject.com/en/2.1/topics/email/
.. _`Twilio`: https://www.twilio.com/
.. _`Smsapi.pl`: https://www.smsapi.pl/
