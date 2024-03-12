
.. _univ.Boolean:

.. |ASN.1| replace:: Boolean

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Boolean(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec

   .. note::

       The |ASN.1| type models a BOOLEAN that can be either TRUE or FALSE.

   .. automethod:: pyasn1.type.univ.Boolean.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   .. automethod:: pyasn1.type.univ.Boolean.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(), subtypeSpec=ConstraintsIntersection())
