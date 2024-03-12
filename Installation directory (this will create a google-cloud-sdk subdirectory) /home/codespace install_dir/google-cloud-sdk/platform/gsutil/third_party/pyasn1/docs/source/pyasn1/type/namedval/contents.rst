
.. _type.namedval:

Enumerating numbers
-------------------

Some ASN.1 types such as :ref:`Integer <univ.Integer>`,
:ref:`Enumerated <univ.Enumerated>` and :ref:`BitString <univ.BitString>`
may enumerate their otherwise numeric values associating them with
human-friendly labels.

.. code-block:: python

   class ErrorStatus(Integer):
   """
   ASN.1 specification:

   error-status
                 INTEGER {
                     noError(0),
                     tooBig(1),
                     noSuchName(2),
                     ...
                  }
   """
   namedValues = NamedValues(
       ('noError', 0), ('tooBig', 1), ('noSuchName', 2)
   )

The enumerated types behave exactly like the non-enumerated ones but,
additionally, values can be referred by labels.

.. code-block:: python

   errorStatus = ErrorStatus('tooBig')

   assert errorStatus == 1


.. toctree::
   :maxdepth: 2

   /pyasn1/type/namedval/namedval
