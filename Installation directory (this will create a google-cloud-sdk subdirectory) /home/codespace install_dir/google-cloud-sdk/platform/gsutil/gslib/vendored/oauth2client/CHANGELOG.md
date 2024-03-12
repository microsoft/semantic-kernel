# CHANGELOG

## v4.1.3

**Note**: oauth2client is deprecated. No more features will be added to the
libraries and the core team is turning down support. We recommend you use
[google-auth](https://google-auth.readthedocs.io) and [oauthlib](http://oauthlib.readthedocs.io/).

* Changed OAuth2 endpoints to use oauth2.googleapis.com variants. (#742)

## v4.1.2

**Note**: oauth2client is deprecated. No more features will be added to the
libraries and the core team is turning down support. We recommend you use
[google-auth](https://google-auth.readthedocs.io) and [oauthlib](http://oauthlib.readthedocs.io/).

Bug fixes:
* Fix packaging issue had erroneously installed the test package. (#688)

## v4.1.1

**Note**: oauth2client is deprecated. No more features will be added to the
libraries and the core team is turning down support. We recommend you use
[google-auth](https://google-auth.readthedocs.io) and [oauthlib](http://oauthlib.readthedocs.io/).

New features:
* Allow passing prompt='consent' via the flow_from_clientsecrets. (#717)

## v4.1.0

**Note**: oauth2client is now deprecated. No more features will be added to the
libraries and the core team is turning down support. We recommend you use
[google-auth](https://google-auth.readthedocs.io) and [oauthlib](http://oauthlib.readthedocs.io/).

New features:
* Allow customizing the GCE metadata service address via an env var. (#704)
* Store original encoded and signed identity JWT in OAuth2Credentials. (#680)
* Use jsonpickle in django contrib, if available. (#676)

Bug fixes:
* Typo fixes. (#668, #697)
* Remove b64 padding from PKCE values, per RFC7636. (#683)
* Include LICENSE in Manifest.in. (#694)
* Fix tests and CI. (#705, #712, #713)
* Escape callback error code in flask_util. (#710)

## v4.0.0

New features:
* New Django samples. (#636)
* Add support for RFC7636 PKCE. (#588)
* Release as a universal wheel. (#665)

Bug fixes:
* Fix django authorization redirect by correctly checking validity of credentials. (#651)
* Correct query loss when using parse_qsl to dict. (#622)
* Switch django models from pickle to jsonpickle. (#614)
* Support new MIDDLEWARE Django 1.10 setting. (#623)
* Remove usage of os.environ.setdefault. (#621)
* Handle missing storage files correctly. (#576)
* Try to revoke token with POST when getting a 405. (#662)

Internal changes:
* Use transport module for GCE environment check. (#612)
* Remove __author__ lines and add contributors.md. (#627)
* Clean up imports. (#625)
* Use transport.request in tests. (#607)
* Drop unittest2 dependency (#610)
* Remove backslash line continuations. (#608)
* Use transport helpers in system tests. (#606)
* Clean up usage of HTTP mocks in tests. (#605)
* Remove all uses of MagicMock. (#598)
* Migrate test runner to pytest. (#569)
* Merge util.py and _helpers.py. (#579)
* Remove httplib2 imports from non-transport modules. (#577)

Breaking changes:
* Drop Python 3.3 support. (#603)
* Drop Python 2.6 support. (#590)
* Remove multistore_file. (#589)

## v3.0.0

* Populate `token_expiry` for GCE credentials. (#473)
* Move GCE metadata interface to a separate module. (#520)
* Populate `scopes` for GCE credentials. (#524)
* Fix Python 3.5 compatibility. (#531)
* Add `oauth2client.contrib.sqlalchemy`, a SQLAlchemy-based credential store. (#527)
* Improve error when an invalid client secret is provided. (#530)
* Add `oauth2client.contrib.multiprocess_storage`. This supersedes the functionality in `oauth2client.contrib.multistore_file`. (#504)
* Pull httplib2 usage into a separate transport module. (#559, #561)
* Refactor all django-related code into `oauth2client.contrib.django_util`. Add `DjangoORMStorage`, remove `FlowField`. (#546)
* Fix application default credentials resolution order. (#570)
* Add configurable timeout for GCE metadata server check. (#571)
* Add warnings when using deprecated `approval_prompt='force'`. (#572)
* Add deprecation warning to `oauth2client.contrib.multistore_file`. (#574)
* (Hygiene) PEP8 compliance and various style fixes (#537, #540, #552, #562)
* (Hygiene) Remove duplicated exception classes in `oauth2client.contrib.appengine`. (#533)

NOTE: The next major release of oauth2client (v4.0.0) will remove the `oauth2client.contrib.multistore_file` module.

## v2.2.0

* Added support to override `token_uri` and `revoke_uri` in `oauth2client.service_account.ServiceAccountCredentials`. (#510)
* `oauth2client.contrib.multistore_file` now handles `OSError` in addition to `IOError` because Windows may raise `OSError` where other platforms will raise `IOError`.
* `oauth2client.contrib.django_util` and `oauth2client.contrib.django_orm` have been updated to support Django 1.8 - 1.10. Versions of Django below 1.8 will not work with these modules.

## v2.1.0

* Add basic support for JWT access credentials. (#503)
* Fix `oauth2client.client.DeviceFlowInfo` to use UTC instead of the system timezone when calculating code expiration.

## v2.0.2

* Fix issue where `flask_util.UserOAuth2.required` would accept expired credentials (#452).
* Fix issue where `flask_util` would fill the session with `Flow` objects (#498).
* Fix issue with Python 3 binary strings in `Flow.step2_exchange` (#446).
* Improve test coverage to 100%.

## v2.0.1

* Making scopes optional on Google Compute Engine `AppAssertionCredentials`
  and adding a warning that GCE won't honor scopes (#419)
* Adding common `sign_blob()` to service account types and a
  `service_account_email` property. (#421)
* Improving error message in P12 factory
  `ServiceAccountCredentials.from_p12_keyfile` when pyOpenSSL is
  missing. (#424)
* Allowing default flags in `oauth2client.tools.run_flow()`
  rather than forcing users to create a dummy argparser (#426)
* Removing `oauth2client.util.dict_to_tuple_key()` from public
  interface (#429)
* Adding `oauth2client.contrib._appengine_ndb` helper module
  for `oauth2client.contrib.appengine` and moving most code that
  uses the `ndb` library into the helper (#434)
* Fix error in `django_util` sample code (#438)

## v2.0.0-post1

* Fix Google Compute Engine breakage (#411, breakage introduced in #387) that
  made it impossible to obtain access tokens
* Implement `ServiceAccountCredentials.from_p12_keyfile_buffer()`
  to allow passing a file-like object in addition to the factory
  constructor that uses a filename directly (#413)
* Implement `ServiceAccountCredentials.create_delegated()`
  to allow upgrading a credential to one that acts on behalf
  of a given subject (#420)

## v2.0.0

* Add django_util (#332)
* Avoid OAuth2Credentials `id_token` going out of sync after a token
  refresh (#337)
* Move to a `contrib` sub-package code not considered a core part of
  the library (#346, #353, #370, #375, #376, #382)
* Add `token_expiry` to `devshell` credentials (#372)
* Move `Storage` locking into a base class (#379)
* Added dictionary storage (#380)
* Added `to_json` and `from_json` methods to all `Credentials`
  classes (#385)
* Fall back to read-only credentials on EACCES errors (#389)
* Coalesced the two `ServiceAccountCredentials`
  classes (#395, #396, #397, #398, #400)

### Special Note About `ServiceAccountCredentials`:
-------------------------------------------------

For JSON keys, you can create a credential via

```py
from oauth2client.service_account import ServiceAccountCredentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    key_file_name, scopes=[...])
```

You can still rely on

```py
from oauth2client.client import GoogleCredentials
credentials = GoogleCredentials.get_application_default()
```

returning these credentials when you set the `GOOGLE_APPLICATION_CREDENTIALS`
environment variable.

For `.p12` keys, construct via

```py
credentials = ServiceAccountCredentials.from_p12_keyfile(
    service_account_email, key_file_name, scopes=[...])
```

though we urge you to use JSON keys (rather than `.p12` keys) if you can.

This is equivalent to the previous method

```py
# PRE-oauth2client 2.0.0 EXAMPLE CODE!
from oauth2client.client import SignedJwtAssertionCredentials

with open(key_file_name, 'rb') as key_file:
    private_key = key_file.read()

credentials = SignedJwtAssertionCredentials(
    service_account_email, private_key, scope=[...])
```

## v1.5.2

* Add access token refresh error class that includes HTTP status (#310)
* Python3 compatibility fixes for Django (#316, #318)
* Fix incremental auth in flask_util (#322)
* Fall back to credential refresh on EDEADLK in multistore_file (#336)

## v1.5.1

* Fix bad indent in `tools.run_flow()` (#301, bug was
  introduced when switching from 2 space indents to 4)

## v1.5.0

* Fix (more like clarify) `bytes` / `str` handling in crypto
  methods. (#203, #250, #272)
* Replacing `webapp` with `webapp2` in `oauth2client.appengine` (#217)
* Added optional `state` parameter to
  `step1_get_authorize_url`. (#219 and #222)
* Added `flask_util` module that provides a Flask extension to aid
  with using OAuth2 web server flow. This provides the same functionality
  as the `appengine.webapp2` OAuth2Decorator, but will work with any Flask
  application regardless of hosting environment. (#226, #273)
* Track scopes used on credentials objects (#230)
* Moving docs to [readthedocs.org][1] (#237, #238, #244)
* Removing `old_run` module. Was deprecated July 2, 2013. (#285)
* Avoid proxies when querying for GCE metadata (to check if
  running on GCE) (#114, #293)

[1]: https://readthedocs.org/

## v1.4.12

* Fix OS X flaky test failure (#189).
* Fix broken OpenSSL import (#191).
* Remove `@util.positional` from wrapped request in `Credentials.authorize()`
  (#196, #197).
* Changing pinned dependencies to `>=` (#200, #204).
* Support client authentication using `Authorization` header (#206).
* Clarify environment check in case where GAE imports succeed but GAE services
  aren't available (#208).

## v1.4.11

* Better environment detection with Managed VMs.
* Better OpenSSL detection in exotic environments.

## v1.4.10

* Update the `OpenSSL` check to be less strict about finding `crypto.py` in
  the `OpenSSL` directory.
* `tox` updates for new environment handling in `tox`.

## v1.4.9

* Ensure that the ADC fails if we try to *write* the well-known file to a
  directory that doesn't exist, but not if we try to *read* from one.

## v1.4.8

* Better handling of `body` during token refresh when `body` is a stream.
* Better handling of expired tokens in storage.
* Cleanup around `openSSL` import.
* Allow custom directory for the `well_known_file`.
* Integration tests for python2 and python3. (!!!)
* Stricter file permissions when saving the `well_known_file`.
* Test cleanup around config file locations.

## v1.4.7

* Add support for Google Developer Shell credentials.
* Better handling of filesystem errors in credential refresh.
* python3 fixes
* Add `NO_GCE_CHECK` for skipping GCE detection.
* Better error messages on `InvalidClientSecretsError`.
* Comment cleanup on `run_flow`.

## v1.4.6

* Add utility function to convert PKCS12 key to PEM. (#115)
* Change GCE detection logic. (#93)
* Add a tox env for doc generation.

## v1.4.5

* Set a shorter timeout for an Application Default Credentials issue on some
  networks. (#93, #101)
* Test cleanup, switch from mox to mock. (#103)
* Switch docs to sphinx from epydoc.

## v1.4.4

* Fix a bug in bytes/string encoding of headers.

## v1.4.3

* Big thanks to @dhermes for spotting and fixing a mess in our test setup.

* Fix a serious issue with tests not being run. (#86, #87, #89)
* Start credentials cleanup for single 2LO/3LO call. (#83, #84)
* Clean up stack traces when re-raising in some places. (#79)
* Clean up doc building. (#81, #82)
* Fixed minimum version for `six` dependency. (#75)

## v1.4.2

* Several small bugfixes related to `six`/py3 support.

## v1.4.1

* Fix a critical bug on import in `oauth2client.tools`.

## v1.4

* Merge python3 branch! Massive thanks due to @pferate and @methane for doing
  the heavy lifting.

* Make `oauth2client.tools` import gracefully if `argparse` isn't present.

* Change `flow.step2_exchange` to preserve the raw `id_token` in the
  `token_response` field.

## v1.3.2

* Quick bugfix for an issue with dict-like arguments to `flow.step2_exchange`,
  which is common in some environments (such as GAE).

## v1.3.1

* Quick bugfix for bad error handling in from_json.

## v1.3

* Added support for the
  [Google Application Default Credentials](https://developers.google.com/accounts/docs/application-default-credentials)
  for more information (thanks @orestica).
* Added support for OAuth2 for devices (#3, thanks @sde-melo).
* The minimum required Python version is now 2.6.
* The `anyjson` submodule has been removed.

* Better exception handling around missing crypto libraries (#56).
* Improve error messages in `AccessTokenRefreshError` (#53, thanks
  @erickoledadevrel).
* Drop `uritemplate` as a dependency.
* Handle X509 certs with PyCrypto (#51, thanks @liujin-google).
* Handle additional failure types on OSX (#32, thanks @simoncadman).
* Better unicode handling with PKCS12 passwords (#31, thanks @jterrace).
* Better retry handling with bad server replies on refresh (#29, thanks
  @kaste).
* Better logging for missing `refresh_token` in server replies (#21).
* Support `login_hint` (#18, thanks @jay0lee).
* Better overwrite options in `django_orm.Storage`. (#2, thanks @lraccomando).


## v1.2

* The use of the `gflags` library is now deprecated, and is no longer a
  dependency. If you are still using the `oauth2client.tools.run()` function
  then include `python-gflags` as a dependency of your application or switch to
  `oauth2client.tools.run_flow`.
* Samples have been updated to use the new `apiclient.sample_tools`, and no
  longer use `gflags`.
* Added support for the experimental Object Change Notification, as found in
  the Cloud Storage API.
* The oauth2client App Engine decorators are now threadsafe.

* Use the following redirects feature of httplib2 where it returns the
  ultimate URL after a series of redirects to avoid multiple hops for every
  resumable media upload request.
* Updated AdSense Management API samples to V1.3
* Add option to automatically retry requests.
* Ability to list registered keys in `multistore_file`.
* User-agent must contain `(gzip)`.
* The `method` parameter for `httplib2` is not positional. This would cause
  spurious warnings in the logging.
* Making OAuth2Decorator more extensible. Fixes Issue 256.
* Update AdExchange Buyer API examples to version v1.2.


## v1.1

* Add PEM support to `SignedJWTAssertionCredentials` (used to only support
  PKCS12 formatted keys). Note that if you use PEM formatted keys you can use
  PyCrypto 2.6 or later instead of OpenSSL.

* Allow deserialized discovery docs to be passed to `build_from_document()`.

* Make `ResumableUploadError` derive from `HttpError`.
* Many changes to move all the closures in `apiclient.discovery` into real
  classes and objects.
* Make `from_json` behavior inheritable.
* Expose the full token response in `OAuth2Client` and `OAuth2Decorator`.
* Handle reasons that are None.
* Added support for NDB based storing of oauth2client objects.
* Update `grant_type` for `AssertionCredentials`.
* Adding a `.revoke()` to Credentials. Closes issue 98.
* Modify `oauth2client.multistore_file` to store and retrieve credentials
  using an arbitrary key.
* Don't accept `403` challenges by default for auth challenges.
* Set `httplib2.RETRIES` to 1.
* Consolidate handling of scopes.
* Upgrade to httplib2 version 0.8.
* Allow setting the `response_type` in `OAuth2WebServerFlow`.
* Ensure that `dataWrapper` feature is checked before using the `data` value.
* HMAC verification does not use a constant time algorithm.

## v1.0

* Changes to the code for running tests and building releases.

## v1.0c3

* In samples and oauth2 decorator, escape untrusted content before displaying it.
* Do not allow credentials files to be symlinks.
* Add XSRF protection to oauth2decorator callback state.
* Handle uploading chunked media by stream.
* Handle passing streams directly to httplib2.
* Add support for Google Compute Engine service accounts.
* Flows no longer need to be saved between uses.
* Change GET to POST if URI is too long. Fixes issue 96.
* Add a `keyring`-based `Storage`.
* More robust picking up JSON error responses.
* Make batch errors align with normal errors.
* Add a Google Compute sample.
* Token refresh to work with old GData API.
* Loading of `client_secrets` JSON file backed by a cache.
* Switch to new discovery path parameters.
* Add support for `additionalProperties` when printing schema'd objects.
* [Fix media upload parameter names.](http://codereview.appspot.com/6374062/)
* oauth2client support for URL-encoded format of exchange token response (e.g.
  Facebook)
* Build cleaner and easier to read docs for dynamic surfaces.

## v1.0c2

* Parameter values of None should be treated as missing. Fixes issue 144.
* Distribute the samples separately from the library source. Fixes issue 155.
* Move all remaining samples over to `client_secrets.json`. Fixes issue 156.
* Make `locked_file.py` understand win32file primitives for better
  awesomeness.

## v1.0c1

* Documentation for the library has
  [switched to epydoc](http://google-api-python-client.googlecode.com/hg/docs/epy/index.html)
* Many improvements for media support:
  + Added media download support, including resumable downloads.
  + Better handling of streams that report their size as 0.
  + Update `MediaUpload` to include `io.Base` and also fix some bugs.
* OAuth bug fixes and improvements.
  + Remove OAuth 1.0 support.
  + Added `credentials_from_code` and `credentials_from_clientsecrets_and_code`.
  + Make oauth2client support Windows-friendly locking.
  + Fix bug in `StorageByKeyName`.
  + Fix `None` handling in Django fields.
    [Fixes issue 128](http://codereview.appspot.com/6298084/).
* [Add epydoc generated docs.](http://codereview.appspot.com/6305043/)
* Move to PEP386 compliant version numbers.
* New and updated samples
  + Ad Exchange Buyer API v1 code samples.
  + Automatically generate Samples wiki page from `README` files.
  + Update Google Prediction samples.
  + Add a Tasks sample that demonstrates Service accounts.
  + [new analytics api samples.](http://codereview.appspot.com/5494058/)
* Convert all inline samples to the Farm API for consistency.

## v1.0beta8

* Updated media upload support.
* Many fixes for batch requests.
* Better handling for requests that don't require a body.
* Fix issues with Google App Engine Python 2.7 runtime.
* Better support for proxies.
* All Storages now have a `.delete()` method.
* Important changes which might break your code:
  + `apiclient.anyjson` has moved to `oauth2client.anyjson`.
  + Some calls, for example, `taskqueue().lease()` used to require a parameter
    named body. In this new release only methods that really need to send a
    body require a body parameter, and so you may get errors about an unknown
    `body` parameter in your call. The solution is to remove the unneeded
    `body={}` parameter.

## v1.0beta7

* Support for
  [batch requests](http://code.google.com/p/google-api-python-client/wiki/Batch).
* Support for
  [media upload](http://code.google.com/p/google-api-python-client/wiki/MediaUpload).
* Better handling for APIs that return something other than JSON.
* Major cleanup and consolidation of the samples.
* Bug fixes and other enhancements:
   72  Defect  Appengine OAuth2Decorator: Convert redirect address to string
   22  Defect  Better error handling for unknown service name or version
   48  Defect  StorageByKeyName().get() has side effects
   50  Defect  Need sample client code for Admin Audit API
   28  Defect  better comments for app engine sample   Nov 9
   63  Enhancement Let OAuth2Decorator take a list of scope
