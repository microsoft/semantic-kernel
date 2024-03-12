
.. _univ.Set:

.. |ASN.1| replace:: Set

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Set(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), sizeSpec=ConstraintsIntersection())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, componentType, subtypeSpec, sizeSpec,
             getComponentByPosition, setComponentByPosition, getComponentByName, setComponentByName, setDefaultComponents,
             getComponentByType, setComponentByType

   .. note::

        The |ASN.1| type models a collection of named ASN.1 components.
        Ordering of the components **is not** preserved upon de/serialisation.

   .. automethod:: pyasn1.type.univ.Set.clone(componentType=None, tagSet=TagSet(), subtypeSpec=ConstraintsIntersection())
   .. automethod:: pyasn1.type.univ.Set.subtype(componentType=None, implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection())
