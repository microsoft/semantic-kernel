urllib3
=======

.. toctree::
   :hidden:
   :maxdepth: 3

   For Enterprise <https://tidelift.com/subscription/pkg/pypi-urllib3?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs>
   v2-roadmap
   sponsors
   user-guide
   advanced-usage
   reference/index
   contributing

urllib3 is a powerful, *user-friendly* HTTP client for Python.
:ref:`Much of the Python ecosystem already uses <who-uses>` urllib3 and you should too.

urllib3 brings many critical features that are missing from the Python
standard libraries:

- Thread safety.
- Connection pooling.
- Client-side TLS/SSL verification.
- File uploads with multipart encoding.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, and brotli encoding.
- Proxy support for HTTP and SOCKS.
- 100% test coverage.

urllib3 is powerful and easy to use:

.. code-block:: python

    >>> import urllib3
    >>> http = urllib3.PoolManager()
    >>> r = http.request('GET', 'http://httpbin.org/robots.txt')
    >>> r.status
    200
    >>> r.data
    'User-agent: *\nDisallow: /deny\n'

For Enterprise
--------------

.. |tideliftlogo| image:: https://nedbatchelder.com/pix/Tidelift_Logos_RGB_Tidelift_Shorthand_On-White_small.png
   :width: 75
   :alt: Tidelift

.. list-table::
   :widths: 10 100

   * - |tideliftlogo|_
     - Professional support for urllib3 is available as part of the `Tidelift
       Subscription`_.  Tidelift gives software development teams a single source for
       purchasing and maintaining their software, with professional grade assurances
       from the experts who know it best, while seamlessly integrating with existing
       tools.

.. _Tidelift Subscription: https://tidelift.com/subscription/pkg/pypi-urllib3?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs
.. _tideliftlogo: https://tidelift.com/subscription/pkg/pypi-urllib3?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs

|learn-more|_ |request-a-demo|_

.. |learn-more| image:: https://raw.githubusercontent.com/urllib3/urllib3/master/docs/images/learn-more-button.png
   :width: 49%
   :alt: Learn more about Tidelift Subscription
.. _learn-more: https://tidelift.com/subscription/pkg/pypi-urllib3?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs

.. |request-a-demo| image:: https://raw.githubusercontent.com/urllib3/urllib3/master/docs/images/demo-button.png
   :width: 49%
   :alt: Request a Demo for the Tidelift Subscription
.. _request-a-demo: https://tidelift.com/subscription/request-a-demo?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs

Installing
----------

urllib3 can be installed with `pip <https://pip.pypa.io>`_

.. code-block:: bash

  $ python -m pip install urllib3

Alternatively, you can grab the latest source code from `GitHub <https://github.com/urllib3/urllib3>`_:

.. code-block:: bash

  $ git clone git://github.com/urllib3/urllib3.git
  $ pip install .

Usage
-----

The :doc:`user-guide` is the place to go to learn how to use the library and
accomplish common tasks. The more in-depth :doc:`advanced-usage` guide is the place to go for lower-level tweaking.

The :doc:`reference/index` documentation provides API-level documentation.

.. _who-uses:

Who uses urllib3?
-----------------

`urllib3 is one of the most downloaded packages on PyPI <https://pypistats.org/top>`_
and is a dependency of many popular Python packages like `Requests <https://requests.readthedocs.io>`_,
`Pip <https://pip.pypa.io>`_, and more!

License
-------

urllib3 is made available under the MIT License. For more details, see `LICENSE.txt <https://github.com/urllib3/urllib3/blob/master/LICENSE.txt>`_.

Contributing
------------

We happily welcome contributions, please see :doc:`contributing` for details.
