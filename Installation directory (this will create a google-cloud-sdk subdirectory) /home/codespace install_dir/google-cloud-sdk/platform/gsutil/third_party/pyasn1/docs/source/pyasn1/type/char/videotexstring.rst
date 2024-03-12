
.. _char.VideotexString:

.. |ASN.1| replace:: VideotexString

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.VideotexString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models character string that can be consumed by sophisticated video
       terminals (by 20-th century standards) to render ascii-art style pictures and animations.

   .. automethod:: pyasn1.type.char.VideotexString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.VideotexString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
