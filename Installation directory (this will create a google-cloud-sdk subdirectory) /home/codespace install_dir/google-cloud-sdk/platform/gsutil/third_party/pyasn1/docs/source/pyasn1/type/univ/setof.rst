
.. _univ.SetOf:

.. |ASN.1| replace:: SetOf

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.SetOf(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), sizeSpec=ConstraintsIntersection())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, componentType, subtypeSpec, sizeSpec,
             getComponentByPosition, setComponentByPosition

   .. note::

        The |ASN.1| type models a collection of elements of a single ASN.1 type.
        Ordering of the components **is not** preserved upon de/serialisation.

   .. automethod:: pyasn1.type.univ.SetOf.clone(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   .. automethod:: pyasn1.type.univ.SetOf.subtype(componentType=None, implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection())
