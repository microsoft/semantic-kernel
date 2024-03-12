
.. _useful.ObjectDescriptor:

.. |ASN.1| replace:: ObjectDescriptor

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.useful.ObjectDescriptor(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet

   .. note::

       The |ASN.1| type models a character string that can accompany the *ObjectIdentifier* type
       to serve as a human-friendly annotation for an OBJECT IDENTIFIER.

   .. automethod:: pyasn1.type.useful.ObjectDescriptor.clone(self, value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.useful.ObjectDescriptor.subtype(self, value=NoValue(), implicitTag=TagSet(), explicitTag=TagSet(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
