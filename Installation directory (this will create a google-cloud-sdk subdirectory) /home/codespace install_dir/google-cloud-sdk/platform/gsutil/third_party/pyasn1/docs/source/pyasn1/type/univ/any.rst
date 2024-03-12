
.. _univ.Any:

.. |ASN.1| replace:: Any

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Any(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='iso-8859-1', binValue=NoValue(),hexValue=NoValue())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec

   .. note::

       The |ASN.1| type models an arbitrary value of an arbitrary type. Typically,
       a selection of types are defined in form of an
       :ref:`open type <opentype.OpenType>` . Technically, the ANY
       value is a serialised representation of some other ASN.1 object.

   .. automethod:: pyasn1.type.univ.Any.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='iso-8859-1')
   .. automethod:: pyasn1.type.univ.Any.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(),encoding='iso-8859-1')
