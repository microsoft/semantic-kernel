
.. _char.IA5String:

.. |ASN.1| replace:: IA5String

.. |encoding| replace:: us-ascii

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.IA5String(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models a basic character string first published in 1963 as an ISO/ITU standard, then it turned into ASCII.

   .. automethod:: pyasn1.type.char.IA5String.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.IA5String.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
