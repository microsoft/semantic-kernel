
.. _char.PrintableString:

.. |ASN.1| replace:: PrintableString

.. |encoding| replace:: us-ascii

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.PrintableString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| models character string that can be entered from a very rudimentary terminals featuring letters,
       digits and punctuation marks.

   .. automethod:: pyasn1.type.char.PrintableString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.PrintableString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
