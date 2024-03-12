
.. _char.TeletexString:

.. |ASN.1| replace:: TeletexString

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.TeletexString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models character string that can be entered from a sophisticated text processing machines
       (by 20-th century standards) featuring letters from multiple alphabets (308 characters!), digits,
       punctuation marks and escape sequences.

   .. automethod:: pyasn1.type.char.TeletexString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.TeletexString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
