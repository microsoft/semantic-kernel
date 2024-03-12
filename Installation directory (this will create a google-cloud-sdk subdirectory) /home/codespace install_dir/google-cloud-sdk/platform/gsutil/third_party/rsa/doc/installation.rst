Installation
============

Installation can be done in various ways. The simplest form uses pip
or easy_install. Either one will work::

    pip install rsa

Depending on your system you may need to use ``sudo pip`` if you want to install
the library system-wide.

Installation from source is also quite easy. Download the source and
then type::

    python setup.py install


The sources are tracked in our `Git repository`_ at
GitHub. It also hosts the `issue tracker`_.

.. _`Git repository`: https://github.com/sybrenstuvel/python-rsa.git
.. _`issue tracker`: https://github.com/sybrenstuvel/python-rsa/issues


Dependencies
------------

Python-RSA has very few dependencies. As a matter of fact, to use it
you only need Python itself. Loading and saving keys does require an
extra module, though: pyasn1. If you used pip or easy_install like
described above, you should be ready to go.


Development dependencies
------------------------

In order to start developing on Python-RSA you need a bit more. Use
pip to install the development requirements in a virtual environment::

    virtualenv -p /path/to/your-python-version python-rsa-venv
    . python-rsa-venv/bin/activate
    pip install -r python-rsa/requirements.txt


Once these are installed, use Git_ to get a copy of the source::

    git clone https://github.com/sybrenstuvel/python-rsa.git
    python setup.py develop

.. _Git: https://git-scm.com/
