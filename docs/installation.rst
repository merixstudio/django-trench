Installation
============
First steps
"""""""""""

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

.. note:: If you're going to use ``djoser`` to handle user authentication make sure you have it installed and included in INSTALLED_APPS. You'll also need ``djangorestframework-jwt`` to support JSON Web Tokens.

Config
""""""

``urls.py``
***********
.. code-block:: python

    urlpatterns = [
        ...,
        url(r'^auth/', include('trench.urls')),
    ]

| If you utilise ``djoser`` and JWT authentication:

.. code-block:: python

    urlpatterns = [
        ...,
        url(r'^auth/', include('trench.urls')), # Base endpoints
        url(r'^auth/', include('djoser.urls')),
        url(r'^auth/', include('trench.urls.djoser')),  # for Token Based Authorization
        url(r'^auth/', include('trench.urls.jwt')), # for JWT
    ]

``settings.py``
***************
| ``django-trench`` supports ``djangorestframework`` built-in Token Based Authentication, as well as JSON Web Tokens. You'll need setup it accordingly:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
            # or / and
            'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
            # or / and
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
    }

Migrations
""""""""""
| Last but not least, run migrations:

.. code-block:: text

    $ ./manage.py migrate
