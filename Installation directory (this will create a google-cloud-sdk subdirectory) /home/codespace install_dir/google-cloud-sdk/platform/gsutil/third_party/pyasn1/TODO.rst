
Things to be done
=================

Big things to tackle, anyone interested is welcome to fork pyasn1, work on
it and come up with a PR!

New codecs
----------

* PER
* OER
* XER
* LWER
* JSON (alinged with existing experimental schemas)

Lazy codecs
-----------

Implement a thin layer over base types to cache pieces
of substrate being decoded till the very moment of ASN.1
object access in the parse tree.

Codecs generator interface
--------------------------

For indefinite length or chunked encoding mode, make codecs
iterable producing/consuming substrate/objects.

ASN.1 schema compiler
---------------------

Ideally, the compiler should parse modern schema files and be
designed to emit code for arbitrary languages (including SQL).

Base types
----------

Implement X.680 constructs, including information schema.

Examples
--------

Add examples, including advanced/obscure use cases.

Documentation
-------------

Document more API, add notes and example snippets.

More fresh modules
------------------

Compile and ship more Pythonized ASN.1 modules for
various ASN.1-based protocols (e.g. Kerberos etc).
Refresh outdated modules in pyasn1-packages.

Minor, housekeeping things
--------------------------

* more PEP8'ing at places
* consider simplifying repr(), otherwise it tend to be too hard to grasp
* Specialize ASN.1 character and useful types

* ber.decoder:

    * suspend codec on underrun error ?
    * present subtypes ?
    * component presence check wont work at innertypeconst
    * type vs value, defaultValue

* ber.encoder:

    * Asn1Item.clone() / shallowcopy issue
    * large length encoder?
    * lookup type by tag first to allow custom codecs for non-base types

* type.useful:

    * may need to implement prettyIn/Out

* type.char:

    * may need to implement constraints

* type.namedtypes

    * type vs tagset name convention

* how untagged TagSet should be initialized?

* type and codecs for Real needs refactoring
