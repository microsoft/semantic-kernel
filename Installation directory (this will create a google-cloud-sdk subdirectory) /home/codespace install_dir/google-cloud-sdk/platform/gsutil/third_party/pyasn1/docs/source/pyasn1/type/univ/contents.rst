
.. _type.univ:

Universal types
---------------

The ASN.1 language defines a collection of core data types
also known as *universal* types.

Some of these types behave like a scalar (e.g. *simple* types) while
the rest are structured types (the standard calls them *constructed*).

Example of simple types include :ref:`Integer <univ.Integer>` or
:ref:`OctetString <univ.OctetString>`. Constructed types like
:ref:`Sequence <univ.Sequence>` embed other types, both simple
and constructed.

.. toctree::
   :maxdepth: 2

   /pyasn1/type/univ/integer
   /pyasn1/type/univ/boolean
   /pyasn1/type/univ/bitstring
   /pyasn1/type/univ/octetstring
   /pyasn1/type/univ/null
   /pyasn1/type/univ/objectidentifier
   /pyasn1/type/univ/real
   /pyasn1/type/univ/enumerated
   /pyasn1/type/univ/any
   /pyasn1/type/univ/setof
   /pyasn1/type/univ/sequenceof
   /pyasn1/type/univ/set
   /pyasn1/type/univ/sequence
   /pyasn1/type/univ/choice

.. _univ.noValue:

.. autoclass:: pyasn1.type.univ.NoValue()
