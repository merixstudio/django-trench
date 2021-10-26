=============
django-trench
=============

.. image:: https://github.com/merixstudio/django-trench/actions/workflows/django-package.yml/badge.svg
  :target: https://github.com/merixstudio/django-trench/actions/workflows/django-package.yml

.. image:: https://codecov.io/gh/merixstudio/django-trench/branch/master/graph/badge.svg?token=U4yDiXUDkb
  :target: https://codecov.io/gh/merixstudio/django-trench

.. image:: https://readthedocs.org/projects/django-trench/badge/?version=latest
   :target: https://django-trench.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/pypi/v/django-trench
   :target: https://pypi.org/project/django-trench/

| **django-trench** provides a set of REST API endpoints to supplement `django-rest-framework`_ with multi-factor authentication (MFA, 2FA). It supports both standard built-in authentication methods, as well as JWT (JSON Web Token).

| We deliver a couple of sample secondary authentication methods including sending OTP based code by:

* E-mail
* SMS / text
* 3rd party mobile apps
* `YubiKey`_

| Developers can easily add their own authentication backends supporting any communication channel.

Features
********

* Easily pluggable and compatible with `django-rest-framework`_
* Allows user to pick an additional authentication method from range of backends defined by a developer. Read more: `backends`_
* Comes out of a box with email, SMS, mobile apps and YubiKey support

Supported versions
******************

* Python 3.7, 3.8, 3.9
* Django 2.0, 2.1, 2.2, 3.0
* Django REST Framework 3.10

| If you are going to use JWT authentication:

* `djangorestframework-simplejwt`_ >= 4.3.0

Quick Start
***********

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
***********

Trench uses Transifex service to translate our package into other languages.

We will appreciate your help with translation.

https://www.transifex.com/merixstudio/django-trench/dashboard/


Demo project
************

You can also check our live `demo`_.

.. _backends: https://django-trench.readthedocs.io/en/latest/backends.html
.. _installation: https://django-trench.readthedocs.io/en/latest/installation.html
.. _demo: https://django-trench.readthedocs.io/en/latest/demo.html
.. _django-rest-framework: http://www.django-rest-framework.org
.. _djoser: https://github.com/sunscrapers/djoser
.. _django-rest-framework-jwt: https://github.com/GetBlimp/django-rest-framework-jwt
.. _djangorestframework-simplejwt: https://github.com/davesque/django-rest-framework-simplejwt
.. _YubiKey: https://www.yubico.com/


Local development
*****************

1. Clone the repo.

2. Crete virtual environment named e.g. :code:`.venv`:

    .. code-block:: shell

        virtualenv .venv

3. Activate the virtual environment:

    .. code-block:: shell

        source .venv/bin/activate

4. Install dependencies:

    .. code-block:: shell

        pip install black mypy
        pip install -r testproject/requirements.txt

5. Set environment variables:

    .. code-block:: shell

        export PYTHONPATH=./testproject
        export DJANGO_SETTINGS_MODULE=settings
        export SECRET_KEY=YOURsecretGOEShere

6. Build your :code:`django-trench` package distribution locally:

    .. code-block:: shell

        python setup.py sdist

    This will create a :code:`dist` directory and place a file named :code:`django-trench-x.x.x.tar.gz`
    where :code:`x.x.x` will be replaced with the current package's version.

7.  Install the :code:`django-trench` package that you just built:

    .. code-block:: shell

        pip install dist/django-trench-x.x.x.tar.gz

    Use the actual distribution file name, the one above is just an example.

8. Check whether the tests are passing:

    .. code-block:: shell

        pytest --cov=testproject/trench testproject/tests/

Remember - anytime you change something in the :code:`django-trench` source code you need to re-build and re-install
the package (steps 6-7) for the changes to be present during e.g. running the tests.
