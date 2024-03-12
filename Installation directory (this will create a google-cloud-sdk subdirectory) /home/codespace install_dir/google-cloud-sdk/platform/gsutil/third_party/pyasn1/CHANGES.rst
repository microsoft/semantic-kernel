
Revision 0.4.2, released 23-11-2017
-----------------------------------

- Fixed explicit tag splitting in chunked encoding mode at
  OctetString and BitString encoders

Revision 0.4.1, released 23-11-2017
-----------------------------------

- ANY DEFINED BY clause support implemented
- Encoders refactored to take either a value (as ASN.1 object)
  or a Python value plus ASN.1 schema
- BitString decoder optimised for better performance when running on
  constructed encoding
- Constructed types' .getComponentBy*() methods accept the `default`
  parameter to return instead if schema object is to be returned
- Constructed types' .getComponentBy*() methods accept the `instantiate`
  parameter to disable automatic inner component instantiation
- The ASN.1 types' `__repr__` implementation reworked for better readability
  at the cost of not being `eval`-compliant
- Most ASN.1 types' `__str__` magic methods (except for OctetString and
  character types) reworked to call `.prettyPrint()` rather than
  `.prettyPrint` calling `__str__` as it was before. The intention is
  to eventually deprecate `.prettyPrint()` in favor of `str()`.
  The other related change is that `str()` of enumerations and boolean
  types will return string label instead of number.
- Fixed Choice.clear() to fully reset internal state of the object
- Sphinx documentation rearranged, simplified and reworded
- The `isValue` singleton is now the only way to indicate ASN.1 schema
  as opposed to ASN.1 schema instance. The legacy `None` initializer
  support has been removed.
- Changed `Null` object initialization behaviour: previous default
  value (`''`) is not set anymore. Thus `Null()` call produces a
  ASN.1 schema object, while `Null('')` - value object.
- Migrated all docs and references from SourceForge
- Imports PEP8'ed
- Fixed ASN.1 encoder not to omit empty substrate produced for inner
  component if the inner component belongs to the simple class (as
  opposed to constructed class)
- Fixed CER/DER encoders to respect tagged CHOICE when ordering
  SET components
- Fixed ASN.1 types not to interfere with the Pickle protocol
- Fixed Sequence/SequenceOf types decoding heuristics in schema-less
  decoding mode

Revision 0.3.7, released 04-10-2017
-----------------------------------

- Fixed ASN.1 time types pickling/deepcopy'ing

Revision 0.3.6, released 21-09-2017
-----------------------------------

- End-of-octets encoding optimized at ASN.1 encoders
- The __getitem__/__setitem__ behavior of Set/Sequence and SetOf/SequenceOf
  objects aligned with the canonical Mapping and Sequence protocols in part
- Fixed crash in ASN.1 encoder when encoding an explicitly tagged
  component of a Sequence

Revision 0.3.5, released 16-09-2017
-----------------------------------

- Codecs signatures unified and pass the options kwargs through the
  call chain
- Explicit tag encoding optimized to avoid unnecessary copying
- End-of-octets sentinel encoding optimized
- Refactored ASN.1 codecs properties to silently enforce proper
  length and chunk size encoding modes
- Fixed DER encoder to always produce primitive encoding
- Fixed crash at SequenceOf native decoder
- Fixed Real.prettyPrint() to fail gracefully on overflow
- Fixed a couple of crashes when debug mode is enabled

Revision 0.3.4, released 07-09-2017
-----------------------------------

- Fixed Native encoder to handle SEQUENCE/SET objects without
  the componentType property
- Added missing component-less SEQUENCE/SET objects dict duck-typing support
- Fixed unnecessary duplicate tags detection at NamesType.tagMap
- Fixed crash at SEQUENCE and SEQUENCE OF CER encoder when running
  in schemaless mode
- Fixed Character types instantiation from OctetString type -- double
  unicode decoding may have scrambled the data

Revision 0.3.3, released 27-08-2017
-----------------------------------

- Improved ASN.1 types instantiation performance
- Improved BER/CER/DER decoder performance by not unconditionally casting
  substrate into str/bytes.
- Fixed exponential index size growth bug when building ambiguous
  NamedTypes tree
- Fixed constructed types decoding failure at BER codec if running
  in schema-less mode
- Fixed crash on prettyPrint'ing a SEQUENCE with no defined components
- Fixed SetOf ordering at CER/DER encoder
- Fixed crash on conditional binascii module import
- Fix to TagSet hash value build

Revision 0.3.2, released 04-08-2017
-----------------------------------

- Fixed SequenceOf/SetOf types initialization syntax to remain
  backward compatible with pyasn1 0.2.*
- Rectified thread safety issues by moving lazy, run-time computation
  into object initializer.
- Fixed .isValue property to return True for empty SetOf/SequenceOf
  objects
- Fixed GeneralizedTime/UTCTime CER/DER codecs to actually get invoked
- Fixed DER/CER encoders handling optional SEQUENCE/SET fields containing
  nested SEQUENCE/SET with optional fields.
- Fixed crash in SequenceOf/SetOf pretty printing and decoding (in some
  cases)
- Fixed documentation markup issues.

Revision 0.3.1, released 26-07-2017
-----------------------------------

- ASN.1 types __init__(), .clone() and .subtype() signatures
  refactored into keyword arguments to simplify their signatures.
- ASN.1 types initialization refactored to minimize the use of
  relatively expensive isNoValue() call
- Lazily pre-populate list of values of Sequence/Set/Choice types
- NamedTypes comparison made more efficient
- More efficient constraints computation and code clean up
- The __getitem__() implementation of some ASN.1 types & tag object
  refactored for better performance
- BER/CER/DER value encoders refactored to produce either tuple of
  bytes or octet-stream depending on what is more optimal
- Reduced the frequency of expensive isinstance() calls
- Tag-related classes optimized, refactored into properties and
  documented.
- The NamedValues implementation refactored to mimic Python dict, its use
  in ASN.1 types refactored into properties and better documented.
  WARNING: this change introduces a deviation from original API.
- NamedType family of classes overhauled, optimized and documented.
- The `componentType` attribute of constructed ASN.1 types turned
  read-only on instances.
- Sequence/Set DER/CER/DER decoder optimized to skip the case of
  reordered components handling when not necessary.
- Tags and constraints-related getter methods refactored into read-only
  instance attributes.
- The .hasValue() method refactored into .isValue property. All ASN.1
  objects now support them, not just scalars.
- The Real.{isInfinity, isPlusInfinity, isMinusInfinity} methods
  refactored into properties and renamed into IsInf, IsPlusInf and isMinusInf
- The end-of-octets type refactored to ensure it is a singleton. Codecs
  changed to rely on that for better performance.
- Codecs lookup made more efficient at BER/CER/DER decoder main loop by
  assigning `typeId` to every ASN.1 type, not just ambiguous ones.
- The .getComponent*() methods of constructed ASN.1 types changed
  to lazily instantiate underlying type rather than return `None`.
  This should simplify its API as initialization like `X[0][1] = 2` becomes
  possible.
  WARNING: this change introduces a deviation from the original API.
- The .setComponent*() methods of SetOf/SequenceOf types changed not
  to allow uninitialized "holes" inside the sequences of their components.
  They now behave similarly to Python lists.
  WARNING: this change introduces a deviation from the original API.
- Default and optional components en/decoding of Constructed type
  refactored towards better efficiency and more control.
- OctetsString and Any decoder optimized to avoid creating ASN.1
  objects for chunks of substrate. Instead they now join substrate
  chunks together and create ASN.1 object from it just once.
- The GeneralizedTime and UTCTime types now support to/from Python
  datetime object conversion.
- Unit tests added for the `compat` sub-package.
- Fixed BitString named bits initialization bug.
- Fixed non-functional tag cache (when running Python 2) at DER decoder.
- Fixed chunked encoding restriction on DER encoder.
- Fixed SET components ordering at DER encoder.
- Fixed BIT STRING & OCTET STRING encoding to be always non-chunked (e.g.
  primitive) at DER encoder
- Fixed `compat.integer.from_bytes()` behaviour on empty input.

Revision 0.2.3, released 25-02-2017
-----------------------------------

- Improved SEQUENCE/SET/CHOICE decoding performance by maintaining a single shared
  NamedType object for all instances of SEQUENCE/SET object.
- Improved INTEGER encoding/decoding by switching to Python's built-in
  integer serialisation functions.
- Improved BitString performance by rebasing it onto Python int type and leveraging
  fast Integer serialisation functions.
- BitString type usability improved in many ways: for example bitshifting and
  numeric operation on BitString is now possible.
- Minor ObjectIdentifier type performance optimization.
- ASN.1 character types refactored to keep unicode contents internally
  (rather than serialised octet stream) and duck-type it directly.
- ASN.1 OctetString initialized from a Python object performs bytes()
  on it when running on Python 3 (used to do str() which is probably
  less logical).
- Missing support for NoValue.__sizeof__ added.
- Added checks to make sure SEQUENCE/SET components being assigned
  match the prototypes.
- Setter methods for constructed types consistently accept matchTags
  and matchConstraints flags to control the strictness of inner
  components compatibility verification. Previously, these checks
  were tied to verifyConstraints flag, now they are all independent.
- General documentation improvements here and there.
- Fix to __reversed__() magic to make it returning an iterator.
- Test suite simplified and unified.
- The __all__ variable added to most of the Python modules.
- The "test" directory renamed into "tests" not to collide with
  the "test" module.

Revision 0.2.2, released 07-02-2017
-----------------------------------

- FIX TO A SECURITY WEAKNESS: define length only decoders could have successfully
  processed indefinite length serialisation.
- FIX TO A SECURITY WEAKNESS: canonical decoders (CER/DER) may have successfully
  consumed non-canonical variations of (otherwise valid) serialisation.
- Broken Enumerated subtyping fixed.

Revision 0.2.1, released 05-02-2017
-----------------------------------

- FIX TO A SECURITY WEAKNESS: BER decoder improperly cached long tags.
- New "native" codec implemented to transform pyasn1 types to Python built-in types and back.
- Switched to new-style classes.
- Sphinx documentation added.
- BitString improvements:

  * simple string of binary digits is now supported as initializer
  * default str() yields string of binary digits (used to yield str(tuple())
  * binValue and hexValue initializers added
  * .asNumbers(), .asOctets() and asInteger() representation added

- Components of constructed ASN.1 types can now be populated with
  uninitialized ASN.1 objects by assigning either noValue sentinel or
  setupComponent() function return in addition to now-legacy None sentinel.
  This should improve code readability.
- NoValue class improved to become a singleton and catch more kinds
  of access to it.
- Compatibility wrappers str2octs() and oct2strs() fixed to run over
  iso-8859-1 encoding.
- Integer changed to emit Real instance if division produces a float.
- True division operation now supported by Integer type.
- The __contains__(), __reverse__() methods implemented for container types
- Iterator protocol support implemented for all container types.
  Warning, warning, warning: this change may potentially affect backward
  compatibility when:

  * user class overrides __getitem__() without overriding __iter__()
  * when user code iterates over SEQUENCE object to get its components (now keys will be yielded)

- Almost complete Python list and dict protocols added to SequenceOf/SetOf and
  Sequence/Set respectively
- Fix to divmod operation implementation in Integer type.
- Fix to IntegerDecoder's precomputed value map on Python 3.
- Fix to base ASN.1 types to run in "unicode_literals" mode.
- Fix to composite constraints "+" operands ordering (AbstractConstraintSet.__radd__)
- Fix to constraints merge in .subtype() -- on merge existing constraints are
  expanded to accommodate new constraints, not the other way round. When existing
  constraints are wrapped in ConstraintsIntersection composite, additional
  constraints being added on subtyping effectively further narrow the set of
  allowed values, which aligns well with the notion of subtyping.
- Fix to NamedTypes methods to handle .getTagMap() returning None
- Fix to Set/Sequence.setDefaultComponents() to return self
- Copyright notice added to non-trivial source code files.
- Author's email changed, copyright extended to 2017

Revision 0.1.9, released 28-09-2015
-----------------------------------

- Wheel distribution format now supported.
- Extensions added to text files, CVS attic flushed.
- Fix to make uninitialized pyasn1 objects failing properly on hash().
- Fix to ObjectIdentifier initialization from unicode string.
- Fix to CER/DER Boolean decoder - fail on non single-octet payload.

Revision 0.1.8, released 22-06-2015
-----------------------------------

- ObjectIdentifier codec fixed to work properly with arc 0 and arc 2 values.
- Explicit limit on ObjectIdentifier arc value size removed.
- Unicode initializer support added to OctetString type and derivatives.
- New prettyPrintType() abstract method implemented to base pyasn1 types
  to facilitate encoding errors analysis.
- The __str__() method implemented to Tag, TagSet and TagMap classes to
  ease encoding errors troubleshooting.
  easing encoding errors
- Fix to SEQUENCE and SET types to give them their private componentTypes
  collection (which is a NamedTypes object) so that they won't collide in
  a MT execution environment.
- Missing T61String,ISO646String character types and ObjectDescriptor useful
  type added.
- Distribute is gone, switched to setuptools completely.
- Missing NamedValues.__repr__() added.
- The base.NoValue() class, that indicates uninitialized ASN.1 object,
  made public.
- The base.NoValue() class instances now support __repr__() what makes
  possible to perform repr() on uninitialized pyasn1 types objects.
- When comparing ASN.1 types, by-tag and/or by-constraints matching
  can now be performed with the isSuperTypeOf()/isSameTypeWith() optional
  flags.
- Constructed types now verify their consistency by invoking 
  isSameTypeWith(matchTags=True, matchConstraints=False) and
  isSuperTypeOf(matchTags=False, matchConstraints=True) for each of their
  components rather than isSuperTypeOf() as it used to be. Constriants check 
  could be enforced to isSameTypeWith() with the strictConstraints=True
  constructed classes attribute.
- Constructed types can now be initialized with new .setComponents() method
  which accepts both var-args and keyword-args. Default repr() modified to
  reflect this change.
- NamedTypes() and NamedValues() made comparable.
- Test coverage extended to cover pyasn1 types __repr__() function.
- The abs(Integer()) & abs(Real()) operation now returns respective pyasn1 
  type, not a Python type.
- More Python magic methods implementations added to Integer & Real classes
  (e.g.  __pos__, __neg__, __round__, __floor__, __ceil__, __trunc__)
- The Integer.__invert__ Python magic method implemented.
- The OctetString.__int__() and .__float__() magic methods implemented.
- Handle the case of null writer at Debug printer.
- BitString encoder/decoder performance improved.
- Built-in debugging is now based on Python logging module.
- Fix to NamedType.__repr__() to work properly.
- Fixes to __repr__() implementation of many built-in ASN.1 types to take into
  account all of their initializers such as tagSet, subtypeSpec etc.
- String typed float initializer to REAL type now supported.
- Float typed mantissa initializer to REAL type for base 2 added.
- Encoding bases 8 and 16 support for REAL type binary encoder added.
- More strict CER/DER encoders added for GeneralizedTime and UTCTime types.
- Asn1Item.hasValue() added to easily distinguish initalized ASN.1 objects
  from uninitialized ones (e.g. pure types).
- Fix to REAL type binary decoder to handle different bases and scale factor.
- Fix to TagSet.repr() to include [obsolete] baseTag information.
- Fix to broken REAL type decoding handling.
- Fix to BitString and OctetString decoders dealing with constructed
  encoding -- it used to be possible to embed other types in substrate.
- DER codec hardened not to tolerate indefinite length encoding/decoding.
- Fix to end-of-octest sentinel handling:

  + require strict two-zeros sentinel encoding
  + recognize EOO sentinel only when explicitly requested by caller
    of the decoder via allowEoo=True parameter (warning: API change)

Revision 0.1.7
--------------

- License updated to vanilla BSD 2-Clause to ease package use
  (http://opensource.org/licenses/BSD-2-Clause).
- Test suite made discoverable by unittest/unittest2 discovery feature.
- Fix to decoder working on indefinite length substrate -- end-of-octets
  marker is now detected by both tag and value. Otherwise zero values may
  interfere with end-of-octets marker.
- Fix to decoder to fail in cases where tagFormat indicates inappropriate
  format for the type (e.g. BOOLEAN is always PRIMITIVE, SET is always 
  CONSTRUCTED and OCTET STRING is either of the two)
- Fix to REAL type encoder to force primitive encoding form encoding.
- Fix to CHOICE decoder to handle explicitly tagged, indefinite length
  mode encoding
- Fix to REAL type decoder to handle negative REAL values correctly. Test
  case added.

Revision 0.1.6
--------------

- The compact (valueless) way of encoding zero INTEGERs introduced in
  0.1.5 seems to fail miserably as the world is filled with broken
  BER decoders. So we had to back off the *encoder* for a while.
  There's still the IntegerEncoder.supportCompactZero flag which
  enables compact encoding form whenever it evaluates to True.
- Report package version on debugging code initialization.

Revision 0.1.5
--------------

- Documentation updated and split into chapters to better match
  web-site contents.
- Make prettyPrint() working for non-initialized pyasn1 data objects. It
  used to throw an exception.
- Fix to encoder to produce empty-payload INTEGER values for zeros
- Fix to decoder to support empty-payload INTEGER and REAL values
- Fix to unit test suites imports to be able to run each from
  their current directory

Revision 0.1.4
--------------

- Built-in codec debugging facility added
- Added some more checks to ObjectIdentifier BER encoder catching
  posible 2^8 overflow condition by two leading sub-OIDs
- Implementations overriding the AbstractDecoder.valueDecoder method
  changed to return the rest of substrate behind the item being processed
  rather than the unprocessed substrate within the item (which is usually
  empty).
- Decoder's recursiveFlag feature generalized as a user callback function
  which is passed an uninitialized object recovered from substrate and
  its uninterpreted payload.
- Catch inappropriate substrate type passed to decoder.
- Expose tagMap/typeMap/Decoder objects at DER decoder to uniform API.
- Obsolete __init__.MajorVersionId replaced with __init__.__version__
  which is now in-sync with distutils.
- Package classifiers updated.
- The __init__.py's made non-empty (rumors are that they may be optimized 
  out by package managers).
- Bail out gracefully whenever Python version is older than 2.4.
- Fix to Real codec exponent encoding (should be in 2's complement form),
  some more test cases added.
- Fix in Boolean truth testing built-in methods
- Fix to substrate underrun error handling at ObjectIdentifier BER decoder
- Fix to BER Boolean decoder that allows other pre-computed
  values besides 0 and 1
- Fix to leading 0x80 octet handling in DER/CER/DER ObjectIdentifier decoder.
  See http://www.cosic.esat.kuleuven.be/publications/article-1432.pdf

Revision 0.1.3
--------------

- Include class name into asn1 value constraint violation exception.
- Fix to OctetString.prettyOut() method that looses leading zero when
  building hex string.

Revision 0.1.2
--------------

- Fix to __long__() to actually return longs on py2k
- Fix to OctetString.__str__() workings of a non-initialized object.
- Fix to quote initializer of OctetString.__repr__()
- Minor fix towards ObjectIdentifier.prettyIn() reliability
- ObjectIdentifier.__str__() is aliased to prettyPrint()
- Exlicit repr() calls replaced with '%r'

Revision 0.1.1
--------------

- Hex/bin string initializer to OctetString object reworked
  (in a backward-incompatible manner)
- Fixed float() infinity compatibility issue (affects 2.5 and earlier)
- Fixed a bug/typo at Boolean CER encoder.
- Major overhawl for Python 2.4 -- 3.2 compatibility:
  + get rid of old-style types
  + drop string module usage
  + switch to rich comparation
  + drop explicit long integer type use
  + map()/filter() replaced with list comprehension
  + apply() replaced with \*/\*\*args
  + switched to use 'key' sort() callback function
  + support both __nonzero__() and __bool__() methods
  + modified not to use py3k-incompatible exception syntax
  + getslice() operator fully replaced with getitem()
  + dictionary operations made 2K/3K compatible
  + base type for encoding substrate and OctetString-based types
  is now 'bytes' when running py3k and 'str' otherwise
  + OctetString and derivatives now unicode compliant.
  + OctetString now supports two python-neutral getters: asOcts() & asInts()
  + print OctetString content in hex whenever it is not printable otherwise
  + in test suite, implicit relative import replaced with the absolute one
  + in test suite, string constants replaced with numerics

Revision 0.0.13
---------------

- Fix to base10 normalization function that loops on univ.Real(0)

Revision 0.0.13b
----------------

- ASN.1 Real type is now supported properly.
- Objects of Constructed types now support __setitem__()
- Set/Sequence objects can now be addressed by their field names (string index)
  and position (integer index).
- Typo fix to ber.SetDecoder code that prevented with schema decoding
  operation.
- Fix to explicitly tagged items decoding support.
- Fix to OctetString.prettyPrint() to better handle non-printable content.
- Fix to repr() workings of Choice objects.

Revision 0.0.13a
----------------

- Major codec re-design.
- Documentation significantly improved.
- ASN.1 Any type is now supported.
- All example ASN.1 modules moved to separate pyasn1-modules package.
- Fix to initial sub-OID overflow condition detection an encoder.
- BitString initialization value verification improved.
- The Set/Sequence.getNameByPosition() method implemented.
- Fix to proper behaviour of PermittedAlphabetConstraint object.
- Fix to improper Boolean substrate handling at CER/DER decoders.
- Changes towards performance improvement:

  + all dict.has_key() & dict.get() invocations replaced with modern syntax
    (this breaks compatibility with Python 2.1 and older).
  + tag and tagset caches introduced to decoder
  + decoder code improved to prevent unnecessary pyasn1 objects creation
  + allow disabling components verification when setting components to
    structured types, this is used by decoder whilst running with schema
    mode.
  + BER decoder for integer values now looks up a small set of pre-computed
    substrate values to save on decoding.
  + a few pre-computed values configured to ObjectIdentifier BER encoder.
  + ChoiceDecoder split-off SequenceOf one to save on unnecessary checks.
  + replace slow hasattr()/getattr() calls with isinstance() introspection.
  + track the number of initialized components of Constructed types to save
    on default/optional components initialization.
  + added a shortcut ObjectIdentifier.asTuple() to be used instead of
    __getitem__() in hotspots.
  + use Tag.asTuple() and pure integers at tag encoder.
  + introduce and use in decoder the baseTagSet attribute of the built-in
    ASN.1 types.

Revision 0.0.12a
----------------

- The individual tag/length/value processing methods of 
  encoder.AbstractItemEncoder renamed (leading underscore stripped)
  to promote overloading in cases where partial substrate processing
  is required.
- The ocsp.py, ldap.py example scripts added.
- Fix to univ.ObjectIdentifier input value handler to disallow negative
  sub-IDs.

Revision 0.0.11a
----------------

- Decoder can now treat values of unknown types as opaque OctetString.
- Fix to Set/SetOf type decoder to handle uninitialized scalar SetOf 
  components correctly.

Revision 0.0.10a
----------------

- API versioning mechanics retired (pyasn1.v1 -> pyasn1) what makes
  it possible to zip-import pyasn1 sources (used by egg and py2exe).

Revision 0.0.9a
---------------

- Allow any non-zero values in Boolean type BER decoder, as it's in
  accordnance with the standard.

Revision 0.0.8a
---------------

- Integer.__index__() now supported (for Python 2.5+).
- Fix to empty value encoding in BitString encoder, test case added.
- Fix to SequenceOf decoder that prevents it skipping possible Choice
  typed inner component.
- Choice.getName() method added for getting currently set component
  name.
- OctetsString.prettyPrint() does a single str() against its value
  eliminating an extra quotes.

Revision 0.0.7a
---------------

- Large tags (>31) now supported by codecs.
- Fix to encoder to properly handle explicitly tagged untagged items.
- All possible value lengths (up to 256^126) now supported by encoders.
- Fix to Tag class constructor to prevent negative IDs.

Revision 0.0.6a
---------------

- Make use of setuptools.
- Constraints derivation verification (isSuperTypeOf()/isSubTypeOf()) fixed.
- Fix to constraints comparation logic -- can't cmp() hash values as it
  may cause false positives due to hash conflicts.

Revision 0.0.5a
---------------

- Integer BER codec reworked fixing negative values encoding bug.
- clone() and subtype() methods of Constructed ASN.1 classes now 
  accept optional cloneValueFlag flag which controls original value
  inheritance. The default is *not* to inherit original value for 
  performance reasons (this may affect backward compatibility).
  Performance penalty may be huge on deeply nested Constructed objects
  re-creation.
- Base ASN.1 types (pyasn1.type.univ.*) do not have default values
  anymore. They remain uninitialized acting as ASN.1 types. In 
  this model, initialized ASN.1 types represent either types with
  default value installed or a type instance.
- Decoders' prototypes are now class instances rather than classes.
  This is to simplify initial value installation to decoder's
  prototype value.
- Bugfix to BitString BER decoder (trailing bits not regarded).
- Bugfix to Constraints use as mapping keys.
- Bugfix to Integer & BitString clone() methods
- Bugix to the way to distinguish Set from SetOf at CER/DER SetOfEncoder
- Adjustments to make it running on Python 1.5.
- In tests, substrate constants converted from hex escaped literals into
  octals to overcome indefinite hex width issue occuring in young Python.
- Minor performance optimization of TagSet.isSuperTagSetOf() method
- examples/sshkey.py added

Revision 0.0.4a
---------------

* Asn1ItemBase.prettyPrinter() -> \*.prettyPrint()

Revision 0.0.3a
---------------

* Simple ASN1 objects now hash to their Python value and don't
  depend upon tag/constraints/etc.
* prettyIn & prettyOut methods of SimplleAsn1Object become public
* many syntax fixes

Revision 0.0.2a
---------------

* ConstraintsIntersection.isSuperTypeOf() and 
  ConstraintsIntersection.hasConstraint() implemented
* Bugfix to NamedValues initialization code
* +/- operators added to NamedValues objects
* Integer.__abs__() & Integer.subtype() added
* ObjectIdentifier.prettyOut() fixes
* Allow subclass components at SequenceAndSetBase
* AbstractConstraint.__cmp__() dropped
* error.Asn1Error replaced with error.PyAsn1Error

Revision 0.0.1a
---------------

* Initial public alpha release
