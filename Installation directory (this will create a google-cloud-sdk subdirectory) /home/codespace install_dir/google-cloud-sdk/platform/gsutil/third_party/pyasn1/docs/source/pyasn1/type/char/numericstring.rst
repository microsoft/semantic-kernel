
.. _char.NumericString:

.. |ASN.1| replace:: NumericString

.. |encoding| replace:: us-ascii

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.NumericString(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| models character string that can be entered from a telephone handset.

   .. automethod:: pyasn1.type.char.NumericString.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.NumericString.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
