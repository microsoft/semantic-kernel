
.. _type.tag:

Tags
----

ASN.1 types formally differ from each other by carrying distinct
tags. A tag is essentially an integer exhibiting certain inner
structure.

Individual tags are usually combined into a collection known as
*TagSet*. Tags and tag sets in pyasn1 are immutable objects assigned
to ASN.1 types as the *tagSet* attribute.

Tags can be appended to one another (in EXPLICIT tagging mode)
or overridden (IMPLICIT tagging mode) ultimately creating a new
ASN.1 subtype.

.. code-block:: python

    class Counter64(Integer):
       """
       ASN.1 specification:

       Counter64 ::=
           [APPLICATION 6]
               IMPLICIT INTEGER
       """
       tagSet = Integer.tagSet.tagImplicitly(
           Tag(tagClassApplication, tagFormatSimple, 6)
       )

    # alternatively
    counter64 = Integer().subtype(
        implicitTag=Tag(tagClassApplication, tagFormatSimple, 6)
    )

ASN.1 types can be related to each other via the *.isSameTypeWith()*,
*.isSuperTypeOf()* and *.isSubTypeOf()* methods. Internally, the *.tagSet*
of the types are compared along with the value constraints
(e.g. *.subtypeSpec*).

.. code-block:: python

    assert Counter64().isSubTypeOf(Integer()) == True
    assert Counter64().isSameTypeWith(Integer()) == False


.. toctree::
   :maxdepth: 2

   /pyasn1/type/tag/tag
   /pyasn1/type/tag/tagset
   /pyasn1/type/tag/tagmap
