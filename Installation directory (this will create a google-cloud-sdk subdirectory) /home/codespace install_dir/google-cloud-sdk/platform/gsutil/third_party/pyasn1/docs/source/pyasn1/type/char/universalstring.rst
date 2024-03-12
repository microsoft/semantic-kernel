
.. _char.UniversalString:

.. |ASN.1| replace:: UniversalString

.. |encoding| replace:: utf-32-be

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.UniversalString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models a Unicode (ISO10646-1) character string implicitly serialised into UTF-32 big endian.

   .. automethod:: pyasn1.type.char.UniversalString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.UniversalString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
