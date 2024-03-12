
.. _univ.SequenceOf:

.. |ASN.1| replace:: SequenceOf

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.SequenceOf(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), sizeSpec=ConstraintsIntersection())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, componentType, subtypeSpec, sizeSpec,
             getComponentByPosition, setComponentByPosition

   .. note::

       The |ASN.1| type models a collection of elements of a single ASN.1 type.
       Ordering of the components **is** preserved upon de/serialisation.
        
   .. automethod:: pyasn1.type.univ.SequenceOf.clone(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   .. automethod:: pyasn1.type.univ.SequenceOf.subtype(componentType=None, implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection())
