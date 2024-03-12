
.. _useful.UTCTime:

.. |ASN.1| replace:: UTCTime

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.useful.UTCTime(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, asDateTime, fromDateTime

   .. note::

       The |ASN.1| type models a character string representing date and time.

       Formal syntax for the *UTCTime* value is:

       * **YYMMDDhhmm[ss]** standing for UTC time, two
         digits for the year, two for the month, two for the day and two
         for the hour, followed by two digits for the minutes and two
         for the seconds if required or

       * a string as above followed by the letter “Z” (denoting a UTC
         time) or

       * a string as above followed by a string **(+|-)hhmm** denoting
         time zone offset relative to UTC

       For example, *170126120000Z* which stands for YYMMDDHHMMSSZ.

   .. automethod:: pyasn1.type.useful.UTCTime.clone(self, value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.useful.UTCTime.subtype(self, value=NoValue(), implicitTag=TagSet(), explicitTag=TagSet(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
