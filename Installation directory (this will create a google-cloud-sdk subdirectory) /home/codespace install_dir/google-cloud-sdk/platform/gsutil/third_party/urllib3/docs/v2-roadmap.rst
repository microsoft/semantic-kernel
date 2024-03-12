v2.0 Roadmap
============

.. important::

   We're seeking `sponsors and supporters for urllib3 v2.0 on Open Collective <https://github.com/sponsors/urllib3>`_.
   There's a lot of work to be done for our small team and we want to make sure
   development can get completed on-time while also fairly compensating contributors
   for the additional effort required for a large release like ``v2.0``.

   Additional information available within the :doc:`sponsors` section of our documentation.


**🚀 Functional API Compatibility**
-----------------------------------

We're maintaining **99% functional API compatibility** to make the
migration an easy choice for most users. Migration from v1.x to v2.x
should be the simplest major version upgrade you've ever completed.

Most changes are either to default configurations, supported Python versions,
and internal implementation details. So unless you're in a specific situation
you should notice no changes! 🎉


v1.26.x Security and Bug Fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thanks to support from `Tidelift <https://tidelift.com/subscription/pkg/pypi-urllib3>`_
we're able to continue supporting v1.26.x releases with
both security and bug fixes for the forseeable future 💖

If your organization relies on urllib3 and is interested in continuing support you can learn
more about the `Tidelift Subscription for Enterprise <https://tidelift.com/subscription/pkg/pypi-urllib3?utm_source=pypi-urllib3&utm_medium=referral&utm_campaign=docs>`_.


**🔐 Modern Security by Default**
---------------------------------

HTTPS requires TLS 1.2+
~~~~~~~~~~~~~~~~~~~~~~~

Greater than 95% of websites support TLS 1.2 or above.
At this point we're comfortable switching the default
minimum TLS version to be 1.2 to ensure high security
for users without breaking services.

Dropping TLS 1.0 and 1.1 by default means you
won't be vulnerable to TLS downgrade attacks
if a vulnerability in TLS 1.0 or 1.1 were discovered in
the future. Extra security for free! By dropping TLS 1.0
and TLS 1.1 we also tighten the list of ciphers we need
to support to ensure high security for data traveling
over the wire.

If you still need to use TLS 1.0 or 1.1 in your application
you can still upgrade to v2.0, you'll only need to set
``ssl_version`` to the proper values to continue using
legacy TLS versions.


Stop Verifying CommonName in Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dropping support the long deprecated ``commonName``
field on certificates in favor of only verifying
``subjectAltName`` to put us in line with browsers and
other HTTP client libraries and to improve security for our users.


Certificate Verification via SSLContext
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default certificate verification is handled by urllib3
to support legacy Python versions, but now we can
rely on Python's certificate verification instead! This
should result in a speedup for verifying certificates
and means that any improvements made to certificate
verification in Python or OpenSSL will be immediately
available.


**✨ Optimized for Python 3.6+**
--------------------------------

In v2.0 we'll be specifically be targeting
CPython 3.6+ and PyPy 7.0+ (compatible with CPython 3.6)
and dropping support Python versions 2.7 and 3.5.

By dropping end-of-life Python versions we're able to optimize
the codebase for Python 3.6+ by using new features to improve
performance and reduce the amount of code that needs to be executed
in order to support legacy versions.


**🔮 Tracing**
--------------

Currently with urllib3 it's tough to get low-level insights into what
how your HTTP client is performing and what your connection information
looks like. In v2.0 we'll be adding tracing and telemetry information
to HTTP response objects including:

- Connection ID
- IP Address resolved by DNS
- Request Method, Target, and Headers
- TLS Version and Cipher
- Certificate Fingerprint, subjectAltName, and Validity Information
- Timings for DNS, Request Data, First Byte in Response


**📜 Type-Hinted APIs**
-----------------------

You'll finally be able to run Mypy or other type-checkers
on code using urllib3. This also means that for IDEs
that support type hints you'll receive better suggestions
from auto-complete. No more confusing with ``**kwargs``!

We'll also add API interfaces to ensure that when
you're sub-classing an interface you're only using
supported public APIs to ensure compatibility and
minimize breakages down the road.


**🎁 ...and many more features!**
---------------------------------

- Top-level ``urllib3.request()`` API
- Open Possibility to Alternate HTTP Implementations
- Translated Guides
- Support Zstandard Compression
- Streaming ``multipart/form-encoded`` Request Data
- More Powerful and Configurable Retry Logic

If there's a feature you don't see here but would like to see
in urllib3 v2.0, there's an open GitHub issue for making
feature suggestions.


**📅 Release and Migration Schedule**
-------------------------------------

We're aiming for all ``v2.x`` features to be released in **mid-to-late 2021**.

Here's what the release and migration schedule will look like leading up
to v2.0 being released:

- Development of ``v2.x`` breaking changes starts.
- Release ``v1.26.0`` with deprecation warnings for ``v2.0.0`` breaking changes.
  This will be the last non-patch release within the ``v1.x`` stream.
- Release ``v2.0.0-alpha1`` once all breaking changes have been completed.
  We'll wait for users to report issues, bugs, and unexpected
  breakages at this stage to ensure the release ``v2.0.0`` goes smoothly.
- Development of remaining ``v2.x`` features starts.
- Release ``v2.0.0`` which will be identical to ``v2.0.0-alpha1``.
- Release ``v2.1.0`` with remaining ``v2.x`` features.

Deprecation warnings within ``v1.26.x`` will be opt-in by default.

**More detailed Application Migration Guide coming soon.**

For Package Maintainers
~~~~~~~~~~~~~~~~~~~~~~~

Since this is the first major release in almost 9 years some users may
be caught off-guard by a new major release of urllib3. We're mitigating this by
trying to make ``v2.x`` API-compatible with ``v1.x``.

If your application or library uses urllib3 and you'd like to be extra
cautious about not breaking your users, you can pin urllib3 like so
until you ensure compatibility with ``v2.x``:

.. code-block:: python

   # 'install_requires' or 'requirements.txt'
   "urllib3>=1.25,<2"

We'd really appreciate testing compatibility
and providing feedback on ``v2.0.0-alpha1`` once released.
