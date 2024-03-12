
.. _type.opentype:

Untyped fields of constructed types
-----------------------------------

To aid data structures flexibility, ASN.1 allows the designer to
leave incomplete field type specification in the
:ref:`Sequence <univ.Sequence>` and :ref:`Set <univ.Set>` types.

To figure out field's type at the run time, a type selector field
must accompany the open type field. The open type situation can
be captured by the :ref:`OpenType <opentype.OpenType>` object.

.. code-block:: python

   algo_map = {
       ObjectIdentifier('1.2.840.113549.1.1.1'): rsaEncryption(),
       ObjectIdentifier('1.2.840.113549.1.1.2'): md2WithRSAEncryption()
   }


   class Algorithm(Sequence):
       """
       Algorithm ::= SEQUENCE {
               algorithm OBJECT IDENTIFIER,
               parameters ANY DEFINED BY algorithm OPTIONAL
       }
       """
       componentType = NamedTypes(
           NamedType('algorithm', ObjectIdentifier()),
           OptionalNamedType('parameters', Any(),
                     openType=OpenType('algorithm', algo_map))
       )


.. toctree::
   :maxdepth: 2

   /pyasn1/type/opentype/opentype
