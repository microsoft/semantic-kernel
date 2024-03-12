Contributing
============

#. **Please sign one of the contributor license agreements below.**
#. Fork the repo, develop and test your code changes, add docs.
#. Make sure that your commit messages clearly describe the changes.
#. Send a pull request.

Here are some guidelines for hacking on ``google-auth-library-python``.

Making changes
--------------

A few notes on making changes to ``google-auth-library-python``.

- If you've added a new feature or modified an existing feature, be sure to
  add or update any applicable documentation in docstrings and in the
  documentation (in ``docs/``). You can re-generate the reference documentation
  using ``nox -s docgen``.

- The change must work fully on the following CPython versions:
  3.6, 3.7, 3.8, 3.9, 3.10 across macOS, Linux, and Windows.

- The codebase *must* have 100% test statement coverage after each commit.
  You can test coverage via ``nox -e cover``.

Testing changes
---------------

To test your changes, run unit tests with ``nox``::

    $ nox -s unit


Running system tests
--------------------

You can run the system tests with ``nox``::

    $ nox -f system_tests/noxfile.py

To run a single session, specify it with ``nox -s``::

    $ nox -f system_tests/noxfile.py -s service_account

First, set the environment variable ``GOOGLE_APPLICATION_CREDENTIALS`` to a valid service account.
See `Creating and Managing Service Account Keys`_ for how to obtain a service account.

Project and Credentials Setup
-------------------------------

Enable the IAM Service Account Credentials API on the project.

To run system tests locally, you will need to set up a data directory ::

    $ mkdir system_tests/data

Your directory should look like this. Follow the instructions below for creating each file. ::

  system_tests/
      data/
        authorized_user.json
        impersonated_service_account.json
        service_account.json


``authorized_user.json``
~~~~~~~~~~~~~~~~~~~~~~~~

Use the `gcloud CLI`_ to get an authorized user file ::

    $ gcloud auth application-default login --scopes=https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,openid

You will see something like::

    Credentials saved to file: [/usr/local/home/.config/gcloud/application_default_credentials.json]

Copy the contents of the file to ``authorized_user.json``.

Open the IAM page of the Google Cloud Console. Grant the user the `Service Account Token Creator Role`.
This will allow the user to impersonate service accounts on the project.

.. _gcloud CLI: https://cloud.google.com/sdk/gcloud/


``service_account.json``
~~~~~~~~~~~~~~~~~~~~~~~~

Follow `Creating and Managing Service Account Keys`_ to create a service account.

Copy the credentials file to ``service_account.json``.

Grant the account associated with ``service_account.json`` the following roles.

- App Engine Admin (for App Engine tests)
- Service Account Token Creator (for impersonated credentials and workload identity federation tests)
- Pub/Sub Viewer (for gRPC tests)
- Storage Object Viewer (for impersonated credentials tests)
- DNS Viewer (for workload identity federation tests)
- GCE Storage Bucket Admin (for downscoping tests)

``impersonated_service_account.json``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow `Creating and Managing Service Account Keys`_ to create a service account.

Copy the credentials file to ``impersonated_service_account.json``.

.. _Creating and Managing Service Account Keys: https://cloud.google.com/iam/docs/creating-managing-service-account-keys

``setup_external_accounts``
~~~~~~~~~~~~~~~~

In order to run the workload identity federation tests, you will need to set up
a Workload Identity Pool, as well as attach relevant policy bindings for this
new resource to our service account. To do this, make sure you have IAM Workload
Identity Pool Admin and Security Admin permissions, and then run:

  $ ./scripts/setup_external_accounts.sh

and then use the output to replace the variables near
the top of system_tests/system_tests_sync/test_external_accounts.py

App Engine System Tests
~~~~~~~~~~~~~~~~~~~~~~~~

To run the App Engine tests, you wil need to deploy a default App Engine service.
If you already have a default service associated with your project, you can skip this step.

Edit ``app.yaml`` so ``service`` is ``default`` instead of ``google-auth-system-tests``.
From ``system_tests/app_engine_test_app`` run the following commands ::

    $ pip install --target lib -r requirements.txt
    $ gcloud app deploy -q app.yaml

After the app is deployed, change ``service`` in ``app.yaml`` back to ``google-auth-system-tests``.
You can now run the App Engine tests: ::

    $ nox -f system_tests/noxfile.py -s app_engine

Compute Engine Tests
^^^^^^^^^^^^^^^^^^^^

These tests cannot be run locally and will be skipped if they are run outside of Google Compute Engine.

grpc Tests
^^^^^^^^^^^^

These tests use the Pub/Sub API. Grant the service account specified by `GOOGLE_APPLICATION_CREDENTIALS`
permissions to list topics. The service account should have at least `roles/pubsub.viewer`.

Coding Style
------------

This library is PEP8 & Pylint compliant. Our Pylint config is defined at
``pylintrc`` for package code and ``pylintrc.tests`` for test code. Use
``nox`` to check for non-compliant code::

   $ nox -s lint

Documentation Coverage and Building HTML Documentation
------------------------------------------------------

If you fix a bug, and the bug requires an API or behavior modification, all
documentation in this package which references that API or behavior must be
changed to reflect the bug fix, ideally in the same commit that fixes the bug
or adds the feature.

To build and review docs use  ``nox``::

   $ nox -s docs

The HTML version of the docs will be built in ``docs/_build/html``

Versioning
----------

This library follows `Semantic Versioning`_.

.. _Semantic Versioning: http://semver.org/

It is currently in major version zero (``0.y.z``), which means that anything
may change at any time and the public API should not be considered
stable.

Contributor License Agreements
------------------------------

Before we can accept your pull requests you'll need to sign a Contributor License Agreement (CLA):

- **If you are an individual writing original source code** and **you own the intellectual property**, then you'll need to sign an `individual CLA <https://developers.google.com/open-source/cla/individual>`__.
- **If you work for a company that wants to allow you to contribute your work**, then you'll need to sign a `corporate CLA <https://developers.google.com/open-source/cla/corporate>`__.

You can sign these electronically (just scroll to the bottom). After that, we'll be able to accept your pull requests.
