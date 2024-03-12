.. :changelog:

History
-------

3.3 (2021-10-13)
++++++++++++++++

- Update to Unicode 14.0.0
- Update to in-line type annotations
- Throw IDNAError exception correctly for some malformed input
- Advertise support for Python 3.10
- Improve testing regime on Github
- Fix Russian typo in documentation

Thanks to Jon Defresne, Hugo van Kemenade, Seth Michael Larson,
Patrick Ventuzelo and Boris Verhovsky for contributions to this
release.

3.2 (2021-05-29)
++++++++++++++++

- Add type hints (Thanks, Seth Michael Larson!)
- Remove support for Python 3.4

3.1 (2021-01-04)
++++++++++++++++

- Ensure license is included in package (Thanks, Julien Schueller)
- No longer mark wheel has universal (Thanks, Matthieu Darbois)
- Test on PowerPC using Travis CI

3.0 (2021-01-01)
++++++++++++++++

- Python 2 is no longer supported (the 2.x branch supports Python 2,
  use "idna<3" in your requirements file if you need Python 2 support)
- Support for V2 UTS 46 test vectors.

2.10 (2020-06-27)
+++++++++++++++++

- Update to Unicode 13.0.0.
- Throws a more specific exception if "xn--" is provided as a label.
- This is expected to be the last version that supports Python 2.

2.9 (2020-02-16)
++++++++++++++++

- Update to Unicode 12.1.0.
- Prohibit A-labels ending with a hyphen (Thanks, Julien Bernard!)
- Future-proofing: Test on Python 3.7 and 3.8, don't immediately
  fail should Python 4 come along.
- Made BSD 3-clause license clearer

2.8 (2018-12-04)
++++++++++++++++

- Update to Unicode 11.0.0.
- Provide more specific exceptions for some malformed labels.

2.7 (2018-06-10)
++++++++++++++++

- Update to Unicode 10.0.0.
- No longer accepts dot-prefixed domains (e.g. ".example") as valid.
  This is to be more conformant with the UTS 46 spec. Users should
  strip dot prefixes from domains before processing.

2.6 (2017-08-08)
++++++++++++++++

- Allows generation of IDNA and UTS 46 table data for different
  versions of Unicode, by deriving properties directly from
  Unicode data.
- Ability to generate RFC 5892/IANA-style table data
- Diagnostic output of IDNA-related Unicode properties and
  derived calculations for a given codepoint
- Support for idna.__version__ to report version
- Support for idna.idnadata.__version__ and
  idna.uts46data.__version__ to report Unicode version of
  underlying IDNA and UTS 46 data respectively.

2.5 (2017-03-07)
++++++++++++++++

- Fix bug with Katakana middle dot context-rule (Thanks, Greg
  Shikhman.)

2.4 (2017-03-01)
++++++++++++++++

- Restore IDNAError to be a subclass of UnicodeError, as some users of
  this library are only looking for the latter to catch invalid strings.

2.3 (2017-02-28)
++++++++++++++++

- Fix bugs relating to deriving IDNAError from UnicodeError.
- More memory footprint improvements (Thanks, Alex Gaynor)

2.2 (2016-12-21)
++++++++++++++++

- Made some changes to the UTS 46 data that should allow Jython to get around
  64kb Java class limits. (Thanks, John A. Booth and Marcin Płonka.)
- In Python 2.6, skip two tests that rely on data not present in that
  Python version's unicodedata module.
- Use relative imports to help downstream users.

2.1 (2016-03-20)
++++++++++++++++

- Memory consumption optimizations. The library should consume significantly
  less memory through smarter data structures being used to represent
  relevant Unicode properties. Many thanks to Shivaram Lingamneni for this
  patch.
- Patches to make library work better with Python 2.6. The core library
  currently works however the unit testing does not. (Thanks, Robert
  Buchholz)
- Better affix all Unicode codepoint properties to a specific version.

2.0 (2015-05-18)
++++++++++++++++

- Added support for Unicode IDNA Compatibility Processing (aka Unicode
  Technical Standard #46). Big thanks to Jon Ribbens who contributed this
  functionality.

1.1 (2015-01-27)
++++++++++++++++

- Use IDNA properties from Unicode 6.3.0. Internet Architecture Board (IAB)
  issued statement recommending against the use of Unicode 7.0.0 until
  issues relating to U+08A1 codepoint are resolved. See http://goo.gl/Ed1n0K
- Identify some cases when label would be too longer to be a legal DNS name
  and raise an exception. (Thanks, Ed Lewis)

1.0 (2014-10-12)
++++++++++++++++

- Update IDNA properties for Unicode 7.0.0.

0.9 (2014-07-18)
++++++++++++++++

- Fix issue with non-UTF-8 environments reading the README file
  now that it contains non-ASCII. (Thanks, Tom Prince)
- Codec functions are useful, so they are separated into their own
  module, rather than just existing for compatibility reasons.
- Add LICENSE file.

0.8 (2014-07-09)
++++++++++++++++

- Added MANIFEST.in for correct source distribution compilation.

0.7 (2014-07-09)
++++++++++++++++

- Filled out missing tests for various functions.
- Fix bug in CONTEXTO validation for Greek lower numeral sign (U+0375)
- Fix bug in CONTEXTO validation for Japanese middle dot (U+30FB)
- Improved documentation
- Move designation to Stable

0.6 (2014-04-29)
++++++++++++++++

- Minor improvements to Python 3 support, tests (Thanks, Derek Wilson)

0.5 (2014-02-05)
++++++++++++++++

- Update IDNA properties for Unicode 6.3.0.

0.4 (2014-01-07)
++++++++++++++++

- Fix trove classifier for Python 3. (Thanks, Hynek Schlawack)

0.3 (2013-07-18)
++++++++++++++++

- Ported to Python 3.

0.2 (2013-07-16)
++++++++++++++++

- Improve packaging.
- More conformant, passes all relevant tests in the Unicode TR46 test suite.

0.1 (2013-05-27)
++++++++++++++++

- First proof-of-concept version.
