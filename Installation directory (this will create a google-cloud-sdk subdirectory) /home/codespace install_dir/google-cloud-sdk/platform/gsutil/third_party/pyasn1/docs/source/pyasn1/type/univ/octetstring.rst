
.. _univ.OctetString:

.. |ASN.1| replace:: OctetString

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.OctetString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='iso-8859-1', binValue=NoValue(),hexValue=NoValue())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec, fromHexString, fromBinaryString

   .. note::

        The |ASN.1| type models an arbitrary string of octets (eight-bit numbers), not printable text string.

   .. automethod:: pyasn1.type.univ.OctetString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='iso-8859-1')
   .. automethod:: pyasn1.type.univ.OctetString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(),encoding='iso-8859-1')
