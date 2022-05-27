=============
django-trench
=============

.. image:: https://cybersecurity-excellence-awards.com/wp-content/uploads/2021/06/badges_2022_Silver.png
   :target: https://cybersecurity-excellence-awards.com/candidates/merixstudio-django-trench-multi-factor-authentication-set/

-----

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
* Django 2.0, 2.1, 2.2, 3.0, 3.1, 3.2
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

.. _backends: https://django-trench.readthedocs.io/en/latest/backends.html
.. _installation: https://django-trench.readthedocs.io/en/latest/installation.html
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

6. Create a symbolic link to the :code:`trench/` module inside the :code:`testproject/` directory to emulate the :code:`trench` package being installed.

    .. code-block:: shell

        # make sure you run this command from the root directory of this project
        ln -s $(pwd)/trench/ $(pwd)/testproject/trench

7. Check whether the tests are passing:

    .. code-block:: shell

        pytest --cov=testproject/trench testproject/tests/

Remember - anytime you change something in the :code:`django-trench` source code you need to re-build and re-install
the package (steps 6-7) for the changes to be present during e.g. running the tests.

8. [OPTIONAL] To make the tests run faster you can try to execute them in parallel.
    To do so you need to install the :code:`pytest-xdist` package and run the tests
    with additional parameter of :code:`-n 8` where :code:`8` stands for the number
    of threads that will be spawned for executing the tests. Depending on the machine
    you're using using this tool can speed up the test execution process up to 5 times.

    .. code-block:: shell

        pytest -n 8 --cov=testproject/trench testproject/tests/
