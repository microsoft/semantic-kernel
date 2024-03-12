
.. _pyasn1:

Library documentation
=====================

As of this moment, pyasn1 library implements all ASN.1 data
types as Python objects in accordance with X.208 standard. Later,
post-1995, revision (X.680) introduced some changes to the schema
language which may not be fully supported by pyasn1. Aside from data
types a collection of data transformation codecs comes with the
pyasn1 package.

As for ASN.1 schema language, pyasn1 package does
not ship any compiler for it. However, there's a tool called
`asn1late <https://github.com/kimgr/asn1ate>`_ which is an ASN.1
grammar parser paired to code generator capable of generating pyasn1
code. So this is an alternative (or at least a good start) to manual
implementation of pyasn1 classes from ASN.1 specification.

Both `pyasn1 <https://github.com/etingof/pyasn1>`_ and
`pyasn1-modules <https://github.com/etingof/pyasn1-modules>`_ libraries
can be used out-of-the-box with Python versions 2.4 through 3.6.
No external dependencies required.

.. _pyasn1-types:

ASN.1 types
-----------

The ASN.1 data description
`language <https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-X.208-198811-W!!PDF-E&type=items>`_
defines a handful of built-in data types. ASN.1 types exhibit different
semantics (e.g. number vs string) and can be distinguished from each other by
:ref:`tags <type.tag>`.

Subtypes can be created on top of base ASN.1 types by adding/overriding the
:ref:`tags <type.tag>` and/or imposing additional
:ref:`constraints <type.constraint>` on accepted values.

ASN.1 types in pyasn1 are Python objects. One or more ASN.1 types
comprise a *schema* describing data structures of unbounded complexity.

.. code-block:: python

   class RSAPublicKey(Sequence):
       """
       ASN.1 specification:

       RSAPublicKey ::= SEQUENCE {
           modulus           INTEGER,  -- n
           publicExponent    INTEGER   -- e
       }
       """
       componentType = NamedTypes(
           NamedType('modulus', Integer()),
           NamedType('publicExponent', Integer())
       )

ASN.1 schema can be "instantiated" by essentially putting some concrete value
into the type container. Such instantiated schema object can still be
used as a schema, but additionally it can play a role of a value in the
context of any applicable operator (e.g. arithmetic etc.).

.. code-block:: python

   rsaPublicKey = RSAPublicKey()

   # ASN.1 SEQUENCE type quacks like Python dict
   rsaPublicKey['modulus'] = 280789907761334970323210643584308373
   rsaPublicKey['publicExponent'] = 65537

Main use of ASN.1 schemas is to guide data transformation. Instantiated
ASN.1 schemas carry concrete data to/from data transformation services.

.. _isValue:

To tell instantiated schema object from just a schema, the *.isValue*
property can come in handy:

.. code-block:: python

   schema = RSAPublicKey()

   # non-instantiated schema
   assert schema.isValue == False

   rsaPublicKey['modulus'] = 280789907761334970323210643584308373

   # partially instantiated schema
   assert schema['modulus'].isValue == True
   assert schema.isValue == False

   rsaPublicKey['publicExponent'] = 65537

   # fully instantiated schema
   assert schema.isValue == True

Copies of existing ASN.1 types can be created with *.clone()* method.
All the existing properties of the prototype ASN.1 object get copied
over the new type unless the replacements are given. Main use-case
for *.clone()* is to instantiate a schema.

.. _clone:

.. code-block:: python

   instantiated_schema_A = Integer(1)

   # ASN.1 INTEGER type quacks like Python int
   assert instantiated_schema_A == 1

   instantiated_schema_B = instantiated_schema_A.clone(2)

   assert instantiated_schema_B == 2

.. _subtype:

New ASN.1 types can be created on top of existing ASN.1 types with
the *subtype()* method. Desired properties of the new type get
merged with the corresponding properties of the old type. Main use-case
for *.subtype()* is to assemble new ASN.1 types by :ref:`tagging <type.tag>`
or applying additional :ref:`constraints <type.constraint>` to accepted
type's values.

.. code-block:: python

   parent_type_schema = Integer()

   child_type_schema = parent_type_schema.subtype(
       explicitTag=Tag(tag.tagClassApplication, tag.tagFormatSimple, 0x06)
   )

   # test ASN.1 type relationships
   assert child_type_schema.isSubtypeOf(parent_type_schema) == True
   assert child_type_schema.isSameTypeWith(parent_type_schema) == False


.. toctree::
   :maxdepth: 2

   /pyasn1/type/univ/contents
   /pyasn1/type/char/contents
   /pyasn1/type/useful/contents

ASN.1 type harness
++++++++++++++++++

The identification and behaviour of ASN.1 types is determined by
:ref:`tags <type.tag>` and :ref:`constraints <type.constraint>`.
The inner structure of *constructed* ASN.1 types is defined by
its :ref:`fields <type.namedtype>` specification.

.. toctree::
   :maxdepth: 2

   /pyasn1/type/tag/contents
   /pyasn1/type/constraint/contents
   /pyasn1/type/namedtype/contents
   /pyasn1/type/opentype/contents
   /pyasn1/type/namedval/contents

.. _pyasn1-codecs:

Serialisation codecs
--------------------

Common use-case for pyasn1 is to instantiate ASN.1 schema with
user-supplied values and pass instantiated schema to the encoder.
The encoder will then turn the data structure into serialised form
(stream of bytes) suitable for storing into a file or sending over
the network.

.. code-block:: python

    value = 1
    instantiated_schema = Integer(value)

    serialised = encode(instantiated_schema)

Alternatively, value and schema can be passed separately:

.. code-block:: python

    value = 1
    schema = Integer()

    serialised = encode(value, asn1Spec=schema)

At the receiving end, a decoder would be invoked and given the
serialised data as received from the network along with the ASN.1
schema describing the layout of the data structures. The outcome
would be an instance of ASN.1 schema filled with values as supplied
by the sender.

.. code-block:: python

    serialised = b'\x01\x01\x01'
    schema = Integer()

    value, _ = decode(serialised, asn1Spec=schema)

    assert value == 1

Many distinct serialisation protocols exist for ASN.1, some are
implemented in pyasn1.

.. toctree::
   :maxdepth: 2

   /pyasn1/codec/ber/contents
   /pyasn1/codec/cer/contents
   /pyasn1/codec/der/contents
   /pyasn1/codec/native/contents
