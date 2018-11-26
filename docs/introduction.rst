About
=====

| **django-trench** provides a set of REST API endpoints to supplement `django-rest-framework`_ with multi-factor authentication (MFA, 2FA). It supports both standard built-in authentication methods, as well as JWT (JSON Web Token). **django-trench** follows the url pattern developed in `djoser`_ library and may act as its supplement.
| We deliver a couple of sample secondary authentication methods including sending OTP based code by email, SMS/text as well as through 3rd party mobile apps. Developers can easily add own auth backend supporting any communication channel.

Features
--------

* Easily plugable and compatible with `django-rest-framework`_ and `djoser`_
* Allows user to pick an additional authentication method from range of backends defined by a developer. Read more: :doc:`backends`
* Comes out of a box with email, SMS add mobile apps support

Requirements
------------

Supported versions
*******************
* Python 3.4, 3.5, 3.6, 3.7
* Django 1.11, 2.0, 2.1
* Django REST Framework 3.8

| If you implement ``djoser`` for authentication:

* `djoser`_ 1.15.0

| If you are going to use JWT authentication:

* `django-rest-framework-jwt`_ 1.11.0

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

| Read further in: :doc:`installation`

Demo project
------------

You can also check our :doc:`demo`.

.. _django-rest-framework: http://www.django-rest-framework.org
.. _djoser: https://github.com/sunscrapers/djoser
.. _django-rest-framework-jwt: https://github.com/GetBlimp/django-rest-framework-jwt
