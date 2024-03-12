:orphan:

oauth2client deprecation
========================

This page is intended for existing users of the `oauth2client`_ who want to
understand the reasons for its deprecation and how this library relates to
``oauth2client``.

.. _oauth2client: https://github.com/google/oauth2client

Reasons for deprecation
-----------------------

#. Lack of ownership: ``oauth2client`` has lacked a definitive owner since
   around 2013.
#. Fragile and ad-hoc design: ``oauth2client`` is the result of several years
   of ad-hoc additions and organic, uncontrolled growth. This has led to a
   library that lacks overall design and cohesion. The convoluted class
   hierarchy is a symptom of this.
#. Lack of a secure, thread-safe, and modern transport: ``oauth2client`` is
   inextricably dependent on `httplib2`_. ``httplib2`` is largely unmaintained
   (although recently there are a small group of volunteers attempting to
   maintain it).
#. Lack of clear purpose and goals: The library is named "oauth2client" but is
   actually a pretty poor OAuth 2.0 client and does a lot of things that have
   nothing to do with OAuth and its related RFCs.

.. _httplib2: https://github.com/httplib2/httplib2

We originally planned to address these issues within ``oauth2client``, however,
we determined that the number of breaking changes needed would be absolutely
untenable for downstream users. It would essentially involve our users having
to rewrite significant portions of their code if they needed to upgrade (either
directly or indirectly through a dependency). Instead, we've chosen to create a
new replacement library that can live side-by-side with ``oauth2client`` and
allow users to migrate gradually. We believe that this was the least painful
option.

Replacement
-----------

The long-term replacement for ``oauth2client`` is this library,
``google-auth``. This library addresses the major issues with oauthclient:

#. Clear ownership: google-auth is owned by the teams that maintain the
   `Cloud Client Libraries`_, `gRPC`_, and the
   `Code Samples for Google Cloud Platform`_.
#. Thought-out design: using the lessons learned from ``oauth2client``, we have
   designed a better module and class hierarchy. The ``v1.0.0`` release of this
   library should provide long-term API stability.
#. Modern, secure, and extensible transports: ``google-auth`` supports
   `urllib3`_, `requests`_, `gRPC`_, and has `legacy support for httplib2`_ to
   help clients migration. It is transport agnostic and has explicit support
   for adding new transports.
#. Clear purpose and goals: ``google-auth`` is explicitly focused on
   Google-specific authentication, especially the server-to-server (service
   account) use case.
 
Because we reduced the scope of the library, there are several features in
``oauth2client`` we intentionally are not supporting in the ``v1.0.0`` release
of ``google-auth``. This does not mean we are not interested in supporting
these features, we just didn't feel they should be part of the initial API.
As downstream users ask for these features we will determine the best way to
serve those use cases without allowing the library to become a dumping ground.
 
The unsupported features are:

#. Support for obtaining user credentials. While this library has support for
   using user credentials, there are no provisions in the core library for
   doing the three-party OAuth 2.0 flow to obtain authorization from a user.
   Instead, we are opting to provide a separate package that does integration
   with `oauthlib`_, `google-auth-oauthlib`_. When that library has a stable
   API, we will consider its inclusion into the core library.
#. Support for storing credentials. The only credentials type that needs to
   be stored are user credentials. We have a `discussion thread`_ on what level
   of support we should do. It's very likely we'll choose to provide an
   abstract interface for this and leave it up to application to provide
   storage implementation specific to their use case. It's also very likely
   that we will also incubate this functionality in the
   `google-auth-oauthlib`_ library before including it in the core library.

.. _Cloud Client Libraries: https://github.com/googlecloudplatform/google-cloud-python
.. _gRPC: http://www.grpc.io/
.. _Code Samples for Google Cloud Platform: https://github.com/googlecloudplatform/python-docs-samples
.. _urllib3: https://urllib3.readthedocs.io
.. _requests: http://python-requests.org
.. _legacy support for httplib2: https://pypi.python.org/pypi/google-auth-httplib2
.. _oauthlib: https://oauthlib.readthedocs.io
.. _google-auth-oauthlib: http://google-auth-oauthlib.readthedocs.io/
.. _discussion thread: https://github.com/GoogleCloudPlatform/google-auth-library-python/issues/33


Post-deprecation support
------------------------

While ``oauth2client`` will not be implementing or accepting any new features,
the ``google-auth`` team will continue to accept bug reports and fix critical
bugs. We will make patch releases as necessary. We have no plans to remove the
library from GitHub or PyPI. Also, we have made sure that the
`google-api-python-client`_ library supports oauth2client and google-auth and
will continue to do so indefinitely.

It is important to note that we will not be adding any features, even if an
external user goes through the trouble of sending a pull request. This policy
is in place because without it we will perpetuate the circumstances that led
to ``oauth2client`` being in the semi-unmaintained state it was in previously.

Some old documentation and examples may use ``oauth2client`` instead of
``google-auth``. We are working to update all of these but it does take a
significant amount of time. Since we are still iterating on user auth, some
samples that use user auth will not be updated until we have settled on a final
interface. If you find any samples you feel should be updated, please
`file a bug`_.

.. _google-api-python-client: https://github.com/google/google-api-python-client
.. _file a bug: https://github.com/GoogleCloudPlatform/google-auth-library-python/issues
