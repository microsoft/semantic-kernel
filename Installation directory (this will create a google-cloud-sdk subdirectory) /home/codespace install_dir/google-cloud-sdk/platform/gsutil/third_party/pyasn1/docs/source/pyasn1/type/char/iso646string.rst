
.. _char.ISO646String:

.. |ASN.1| replace:: ISO646String

.. |encoding| replace:: us-ascii

|ASN.1| type
------------

.. autoclass:: pyasn1.type.char.ISO646String(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap

   .. note::

       The |ASN.1| type is an alias to the :py:class:`VisibleString` type
       
   .. automethod:: pyasn1.type.char.ISO646String.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.char.ISO646String.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
