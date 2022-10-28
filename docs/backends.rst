Authentication backends
=======================

| ``django-trench`` comes with some predefined authentication methods.
| Custom backends can be easily added by inheriting from ``AbstractMessageDispatcher`` class.

Built-in backends
"""""""""""""""""

E-mail
*****

This basic method uses built-in Django email backend.
Check out the `Django's documentation`_ on this topic.

.. code-block:: python

    TRENCH_AUTH = {
        (...)
        'MFA_METHODS': {
            'email': {
                'VERBOSE_NAME': 'email',
                'VALIDITY_PERIOD': 60 * 10,
                'HANDLER': 'trench.backends.basic_mail.SendMailBackend',
                'SOURCE_FIELD': 'email',
                'EMAIL_SUBJECT': 'Your verification code',
                'EMAIL_PLAIN_TEMPLATE': 'trench/backends/email/code.txt',
                'EMAIL_HTML_TEMPLATE': 'trench/backends/email/code.html',
            },
            ...,
        },
    }

``EMAIL_PLAIN_TEMPLATE`` and ``EMAIL_HTML_TEMPLATE`` are paths to templates
that are used to render email content.

These templates receive ``code`` variable in the context, which is the generated OTP code.

Text / SMS
**********

| SMS backends sends out text messages with `Twilio`_ or `SMS API`_. Credentials can be set in method's specific settings.

Using Twilio
------------

| If you are using Twilio service for sending out Text messages then you need to set ``TWILIO_ACCOUNT_SID`` and ``TWILIO_AUTH_TOKEN`` environment variables for Twilio API client to be used as credentials.

.. code-block:: python

    TRENCH_AUTH = {
        "MFA_METHODS": {
            "sms_twilio": {
                VERBOSE_NAME: _("sms_twilio"),
                VALIDITY_PERIOD: 30,
                HANDLER: "trench.backends.twilio.TwilioMessageDispatcher",
                SOURCE_FIELD: "phone_number",
                TWILIO_VERIFIED_FROM_NUMBER: "+48 123 456 789",
            },
        },
    }

:SOURCE_FIELD: Defines the field name in your ``AUTH_USER_MODEL`` to be looked up and used as field containing the phone number of the recipient of the OTP code.
:TWILIO_VERIFIED_FROM_NUMBER: This will be used as the sender's phone number. Note: this number must be verified in the Twilio's client panel.

Using SMS API
-------------

.. code-block:: python

    TRENCH_AUTH = {
        "MFA_METHODS": {
            "sms_api": {
                "VERBOSE_NAME": _("sms_api"),
                "VALIDITY_PERIOD": 30,
                "HANDLER": "trench.backends.sms_api.SMSAPIMessageDispatcher",
                "SOURCE_FIELD": "phone_number",
                "SMSAPI_ACCESS_TOKEN": "YOUR SMSAPI TOKEN",
                "SMSAPI_FROM_NUMBER": "YOUR REGISTERED NUMBER",
            }
        }
    }


:SOURCE_FIELD: Defines the field name in your ``AUTH_USER_MODEL`` to be looked up and used as field containing the phone number of the recipient of the OTP code.
:SMSAPI_ACCESS_TOKEN: Access token obtained from `SMS API`_
:SMSAPI_FROM_NUMBER: This will be used as the sender's phone number.

Authentication apps
*******************
| This backend returns OTP based QR link to be scanned by apps like Google Authenticator and Authy.

**Important note:** validity period varies between apps. Use the right value you
find in a given provider's docs. Setting the wrong value will lead to an error with
validating MFA code.

.. code-block:: python

    TRENCH_AUTH = {
        "MFA_METHODS": {
            "app": {
                "VERBOSE_NAME": _("app"),
                "VALIDITY_PERIOD": 30,
                "USES_THIRD_PARTY_CLIENT": True,
                "HANDLER": "trench.backends.application.ApplicationMessageDispatcher",
            }
        }
    }

YubiKey
*******

.. code-block:: python

    TRENCH_AUTH = {
        "MFA_METHODS": {
            "yubi": {
                "VERBOSE_NAME": _("yubi"),
                "HANDLER": "trench.backends.yubikey.YubiKeyMessageDispatcher",
                "YUBICLOUD_CLIENT_ID": "YOUR KEY",
            }
        }
    }

:YUBICLOUD_CLIENT_ID: Your client ID obtained from `Yubico`_.

Adding custom MFA backend
"""""""""""""""""""""""""

| Basing on provided examples you can create your own handler class, which inherits from ``AbstractMessageDispatcher``.

.. code-block:: python

    from trench.backends.base import AbstractMessageDispatcher


    class YourMessageDispatcher(AbstractMessageDispatcher):
        def dispatch_message(self) -> DispatchResponse:
            try:
                # dispatch the message through the channel of your choice
                return SuccessfulDispatchResponse(details=_("Code was sent."))
            except Exception as cause:
                return FailedDispatchResponse(details=str(cause))

.. _`Django's documentation`: https://docs.djangoproject.com/en/3.2/topics/email/
.. _`Twilio`: https://www.twilio.com/
.. _`SMS API`: https://www.smsapi.pl/
.. _`Yubico`: https://www.yubico.com/
