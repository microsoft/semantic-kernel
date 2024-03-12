
.. _char.UTF8String:

.. |ASN.1| replace:: UTF8String

.. |encoding| replace:: utf-8

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.UTF8String(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models a Unicode (ISO10646-1) character string implicitly serialised into UTF-8.
       
   .. automethod:: pyasn1.type.char.UTF8String.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.UTF8String.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
