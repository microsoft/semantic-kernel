
.. _univ.Real:

.. |ASN.1| replace:: Real

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Real(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec, isInf, isPlusInf, isMinusInf

   .. note::

       The |ASN.1| type models a rational number of arbitrary precision.

   .. automethod:: pyasn1.type.univ.Real.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   .. automethod:: pyasn1.type.univ.Real.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(), subtypeSpec=ConstraintsIntersection())
