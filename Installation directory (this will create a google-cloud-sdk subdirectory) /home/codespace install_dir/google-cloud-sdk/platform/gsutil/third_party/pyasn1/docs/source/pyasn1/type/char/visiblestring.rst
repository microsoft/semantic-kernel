
.. _char.VisibleString:

.. |ASN.1| replace:: VisibleString

.. |encoding| replace:: us-ascii

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.VisibleString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type models a character string that can hold any "graphical" characters
       mixed with control ones to select particular alphabet.
       
   .. automethod:: pyasn1.type.char.VisibleString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.VisibleString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
