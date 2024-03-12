Contributing
============

urllib3 is a community-maintained project and we happily accept contributions.

If you wish to add a new feature or fix a bug:

#. `Check for open issues <https://github.com/urllib3/urllib3/issues>`_ or open
   a fresh issue to start a discussion around a feature idea or a bug. There is
   a *Contributor Friendly* tag for issues that should be ideal for people who
   are not very familiar with the codebase yet.
#. Fork the `urllib3 repository on Github <https://github.com/urllib3/urllib3>`_
   to start making your changes.
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.
#. Format your changes with black using command `$ nox -rs format` and lint your
   changes using command `nox -rs lint`.
#. Send a pull request and bug the maintainer until it gets merged and published.


Setting up your development environment
---------------------------------------

In order to setup the development environment all that you need is
`nox <https://nox.thea.codes/en/stable/index.html>`_ installed in your machine::

  $ pip install --user --upgrade nox


Running the tests
-----------------

We use some external dependencies, multiple interpreters and code coverage
analysis while running test suite. Our ``noxfile.py`` handles much of this for
you::

  $ nox --reuse-existing-virtualenvs --sessions test-2.7 test-3.7
  [ Nox will create virtualenv if needed, install the specified dependencies, and run the commands in order.]
  nox > Running session test-2.7
  .......
  .......
  nox > Session test-2.7 was successful.
  .......
  .......
  nox > Running session test-3.7
  .......
  .......
  nox > Session test-3.7 was successful.

There is also a nox command for running all of our tests and multiple python
versions.::

  $ nox --reuse-existing-virtualenvs --sessions test

Note that code coverage less than 100% is regarded as a failing run. Some
platform-specific tests are skipped unless run in that platform.  To make sure
the code works in all of urllib3's supported platforms, you can run our ``nox``
suite::

  $ nox --reuse-existing-virtualenvs --sessions test
  [ Nox will create virtualenv if needed, install the specified dependencies, and run the commands in order.]
  .......
  .......
  nox > Session test-2.7 was successful.
  nox > Session test-3.4 was successful.
  nox > Session test-3.5 was successful.
  nox > Session test-3.6 was successful.
  nox > Session test-3.7 was successful.
  nox > Session test-3.8 was successful.
  nox > Session test-pypy was successful.

Our test suite `runs continuously on Travis CI
<https://travis-ci.org/urllib3/urllib3>`_ with every pull request.

To run specific tests or quickly re-run without nox recreating the env, do the following::

  $ nox --reuse-existing-virtualenvs --sessions test-3.8 -- pyTestArgument1 pyTestArgument2 pyTestArgumentN
  [ Nox will create virtualenv, install the specified dependencies, and run the commands in order.]
  nox > Running session test-3.8
  nox > Re-using existing virtual environment at .nox/test-3-8.
  .......
  .......
  nox > Session test-3.8 was successful.

After the ``--`` indicator, any arguments will be passed to pytest.
To specify an exact test case the following syntax also works:
``test/dir/module_name.py::TestClassName::test_method_name``
(eg.: ``test/with_dummyserver/test_https.py::TestHTTPS::test_simple``).
The following argument is another valid example to pass to pytest: ``-k test_methode_name``.
These are useful when developing new test cases and there is no point
re-running the entire test suite every iteration. It is also possible to
further parameterize pytest for local testing.

For all valid arguments, check `the pytest documentation
<https://docs.pytest.org/en/stable/usage.html#stopping-after-the-first-or-n-failures>`_.

Releases
--------

A release candidate can be created by any contributor by creating a branch
named ``release-x.x`` where ``x.x`` is the version of the proposed release.

- Update ``CHANGES.rst`` and ``urllib3/__init__.py`` with the proper version number
  and commit the changes to ``release-x.x``.
- Open a pull request to merge the ``release-x.x`` branch into the ``master`` branch.
- Integration tests are run against the release candidate on Travis. From here on all
  the steps below will be handled by a maintainer so unless you receive review comments
  you are done here.
- Once the pull request is squash merged into master the merging maintainer
  will tag the merge commit with the version number:

  - ``git tag -a 1.24.1 [commit sha]``
  - ``git push origin master --tags``

- After the commit is tagged Travis will build the tagged commit and upload the sdist and wheel
  to PyPI and create a draft release on GitHub for the tag. The merging maintainer will
  ensure that the PyPI sdist and wheel are properly uploaded.
- The merging maintainer will mark the draft release on GitHub as an approved release.
