
.. _type.namedtype:

Fields of constructed types
---------------------------

The :ref:`Sequence <univ.Sequence>`, :ref:`Set <univ.Set>` and
:ref:`Choice <univ.Choice>` ASN.1 types embed other ASN.1 types
as named fields.

Each field can be expressed via the :ref:`NamedType <namedtype.NamedType>`
object while the individual fields are brought together by the
:ref:`NamedTypes <namedtype.NamedTypes>` object.

Ultimately, the fields get attached to the ASN.1 type's *.componentType*
attributes.

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

.. toctree::
   :maxdepth: 2

   /pyasn1/type/namedtype/namedtype
   /pyasn1/type/namedtype/optionalnamedtype
   /pyasn1/type/namedtype/defaultednamedtype
   /pyasn1/type/namedtype/namedtypes
