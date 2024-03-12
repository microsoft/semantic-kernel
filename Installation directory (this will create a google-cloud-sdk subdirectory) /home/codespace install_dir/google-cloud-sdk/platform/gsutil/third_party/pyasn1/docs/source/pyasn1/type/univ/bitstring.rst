
.. _univ.BitString:

.. |ASN.1| replace:: BitString

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.BitString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), namedValues=NamedValues(),binValue=NoValue(), hexValue=NoValue())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec, asInteger, asNumbers, asOctets, asBinary, fromHexString, fromBinaryString, fromOctetString

   .. note::

        The |ASN.1| type models an arbitrary sequence of bits.

   .. automethod:: pyasn1.type.univ.BitString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), namedValues=NamedValues(),binValue=NoValue(), hexValue=NoValue())
   .. automethod:: pyasn1.type.univ.BitString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), , namedValues=NamedValues(),binValue=NoValue(), hexValue=NoValue())
