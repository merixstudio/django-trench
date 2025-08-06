About
=====

| **django-trench** provides a set of REST API endpoints to supplement `django-rest-framework`_ with multi-factor authentication (MFA, 2FA). It supports both standard built-in authentication methods, as well as JWT (JSON Web Token).
| We deliver a couple of sample secondary authentication methods including sending OTP based code by email, SMS/text as well as through 3rd party mobile apps or utilising YubiKey. Developers can easily add their own auth backend supporting any communication channel.

Features
--------

* Easily pluggable and compatible with `django-rest-framework`_
* Allows user to pick an additional authentication method from range of backends defined by a developer. Read more: `backends`_
* Comes out of a box with email, SMS, mobile apps and YubiKey support

Requirements
------------

* Python
* Django
* Django REST Framework

Supported versions
******************

* Python 3.7, 3.8. 3.9, 3.10
* Django 2.x, 3.x, 4.x
* Django REST Framework >= 3.10

Quick Start
-----------

1. Install the package using pip:

.. code-block:: python

    pip install django-trench

or add it to your requirements file.

2. Add ``trench`` library to INSTALLED_APPS in your app settings file:

.. code-block:: python

    INSTALLED_APPS = (
        ...,
        'rest_framework',
        'rest_framework.authtoken',  # In case of implementing Token Based Authentication
        ...,
        'trench',
    )

3. Run migrations

| Read further in: `installation`_.

Translation
-----------

| Trench uses Transifex service to translate our package into other languages.
| We will appreciate your help with `translation`_.

.. _backends: https://django-trench.readthedocs.io/en/latest/backends.html
.. _installation: https://django-trench.readthedocs.io/en/latest/installation.html
.. _demo: https://django-trench.readthedocs.io/en/latest/demo.html
.. _django-rest-framework: http://www.django-rest-framework.org
.. _translation: https://www.transifex.com/merixstudio/django-trench/dashboard/
