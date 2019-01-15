Examples
========
| In order to let you familiarise with the library, a fully working test project is provided in the repository.
| It allows you to run ``django-trench`` with basic settings as well as play with it thanks to a sample frontend app.

Launching a sample app
**********************
1. Clone the repository:

.. code-block:: text

    $ git clone https://github.com/merixstudio/django-trench.git

2. Check ``testproject`` directory and adjust ``settings.py`` inside ``testapp`` according to :doc:`installation` and :doc:`settings` if necessary.

3. Make sure you have ``docker`` and ``docker-compose`` installed. Use ``Makefile`` to run backend:

.. code-block:: text

    $ make build
    $ make migrate

3. Run the app using command:

.. code-block:: text

    $ make client

| Frontend app is availabe on http://localhost:3000/ and expects backend running on http://localhost:8000/

Basic usage
***********

| You can create an admin user to be able to access admin panel ``http://localhost:8000/admin``:

.. code-block:: text

    $ make create_admin

| From built-in admin panel you can add users and setup credentials.
| Alternatively ``djoser`` endpoints can be used to manage users in through REST requests. Read further in `djoser`_ docs.

.. _`djoser`: https://djoser.readthedocs.io/en/stable/sample_usage.html

| Let's login:

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/login/ -d 'username=admin&password=yourpassword'


| In the following request you'll need a provided ``token`` for authorization.
|
| To activate an email authentication:

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/email/activate/ -d 'method=email'
    -H 'Authorization: JWT [token provided]'


| Check the code and confirm:

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/email/activate/confirm/ -d 'code=[code provided]'
    -H 'Authorization: JWT [token provided]'

| In response you'll receive a batch of backup codes.
|
| Let's login again and check if an extra authentication works.

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/login/ -d 'username=admin&password=yourpassword'

    {
        "ephemeral_token": "token",
        "method": "email",
        "other_methods": []
    }

| Right, we need an extra step to get logged in. Let's get a code:

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/code/request/ -d 'method=email'
    -H 'Authorization: JWT [token provided]'

| Now we only need pass on the code and token:

.. code-block:: text

    $ curl -X POST http://localhost:8000/auth/login/code/
    -d 'code=[code from previous step]&ephemeral_token=[ephemeral_token from step before]'

    {
        "token": "JWT token",
    }

All right, we're in!
