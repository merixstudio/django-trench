Installation
============

First steps
"""""""""""

1. Install the package using pip:

.. code-block:: python

    pip install django-trench

or add it to your requirements file.

2. Add ``trench`` library to ``INSTALLED_APPS`` in your ``settings.py`` file:

.. code-block:: python

    INSTALLED_APPS = (
        ...,
        'rest_framework',
        'rest_framework.authtoken',  # In case of implementing Token Based Authentication
        ...,
        'trench',
    )

Setup
"""""

With JWT authentication
***********************

1. Include Django Trench's URLs to your application:

.. code-block:: python

    urlpatterns = [
        ...,
        url(r'^auth/', include('trench.urls')),
        url(r'^auth/', include('trench.urls.jwt')),
    ]


2. Adjust your ``settings.py`` file like so:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
    }


With token authentication
*************************

1. Include Django Trench's URLs to your application:

.. code-block:: python

    urlpatterns = [
        ...,
        url(r'^auth/', include('trench.urls')),
        url(r'^auth/', include('trench.urls.authtoken')),
    ]


2. Adjust your ``settings.py`` file like so:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
        ),
    }

3. Add ``rest_framework.authtoken`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        ...,
        'rest_framework.authtoken',
    )

Migrations
""""""""""

| Last but not least, run migrations:

.. code-block:: shell

    python manage.py migrate
