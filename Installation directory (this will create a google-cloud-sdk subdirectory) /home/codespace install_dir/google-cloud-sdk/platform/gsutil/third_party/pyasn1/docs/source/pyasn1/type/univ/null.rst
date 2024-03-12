
.. _univ.Null:

.. |ASN.1| replace:: Null

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Null(value=NoValue(), tagSet=TagSet())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec

   .. note::

       The |ASN.1| type models ASN.1 NULL.

   .. automethod:: pyasn1.type.univ.Null.clone(value=NoValue(), tagSet=TagSet())
   .. automethod:: pyasn1.type.univ.Null.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag())
