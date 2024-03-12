
.. _type.constraint:

Constraints
-----------

ASN.1 standard has a built-in way of limiting the set of values
a type can possibly have. Imposing value constraints on an ASN.1
type, together with :ref:`tagging <type.tag>`, is a way of creating
a more specialized subtype of an ASN.1 type.

The pyasn1 implementation represents all flavors of constraints,
as well as their combinations, as immutable Python objects. Ultimately,
they get attached to ASN.1 type object at a *.subtypeSpec* attribute.

.. code-block:: python

   class Age(Integer):
       """
       ASN.1 specification:

       Age ::= INTEGER (0..120)
       """
       subtypeSpec = ValueRangeConstraint(0, 120)


.. toctree::
   :maxdepth: 2

   /pyasn1/type/constraint/singlevalue
   /pyasn1/type/constraint/containedsubtype
   /pyasn1/type/constraint/valuerange
   /pyasn1/type/constraint/valuesize
   /pyasn1/type/constraint/permittedalphabet


Logic operations on constraints
+++++++++++++++++++++++++++++++

Sometimes multiple constraints are applied on an ASN.1 type. To capture
this situation, individual constraint objects can be glued together
by the logic operator objects.

The logic operators are Python objects that exhibit similar behaviour
as the constraint objects do with the only difference that logic operators
are instantiated on the constraint and logic operator objects, not on the
bare values.

.. code-block:: python

   class PhoneNumber(NumericString):
       """
       ASN.1 specification:

       PhoneNumber ::=
           NumericString (FROM ("0".."9")) (SIZE (10))
       """
       subtypeSpec = ConstraintsIntersection(
           ValueRangeConstraint('0', '9'), ValueSizeConstraint(10)
       )

.. toctree::
   :maxdepth: 2

   /pyasn1/type/constraint/constraintsintersection
   /pyasn1/type/constraint/constraintsunion
   /pyasn1/type/constraint/constraintsexclusion
