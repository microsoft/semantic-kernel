
.. _univ.Enumerated:

.. |ASN.1| replace:: Enumerated

|ASN.1| type
------------

.. autoclass:: pyasn1.type.univ.Enumerated(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), namedValues=NamedValues())
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, effectiveTagSet, tagMap, subtypeSpec, namedValues

   .. note::

        The |ASN.1| type models bounded set of named integer values. Other than that, it is identical to
        the *Integer* class.

   .. automethod:: pyasn1.type.univ.Enumerated.clone(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), namedValues=NamedValues())
   .. automethod:: pyasn1.type.univ.Enumerated.subtype(value=NoValue(), implicitTag=Tag(), explicitTag=Tag(),subtypeSpec=ConstraintsIntersection(), namedValues=NamedValues())
