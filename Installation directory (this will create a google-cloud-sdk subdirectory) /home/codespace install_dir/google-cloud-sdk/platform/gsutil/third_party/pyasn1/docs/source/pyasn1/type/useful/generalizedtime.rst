
.. _useful.GeneralizedTime:

.. |ASN.1| replace:: GeneralizedTime

.. |encoding| replace:: iso-8859-1

|ASN.1| type
------------

.. autoclass:: pyasn1.type.useful.GeneralizedTime(value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   :members: isValue, isSameTypeWith, isSuperTypeOf, tagSet, asDateTime, fromDateTime

   .. note::


       The |ASN.1| type models a character string representing date and time
       in many different formats.

       Formal syntax for the *GeneralizedTime* value is:

       * **YYYYMMDDhh[mm[ss[(.|,)ffff]]]** standing for a local time, four
         digits for the year, two for the month, two for the day and two
         for the hour, followed by two digits for the minutes and two
         for the seconds if required, then a dot (or a comma), and a
         number for the fractions of second or

       * a string as above followed by the letter “Z” (denoting a UTC
         time) or

       * a string as above followed by a string **(+|-)hh[mm]** denoting
         time zone offset relative to UTC

       For example, *20170126120000Z* stands for YYYYMMDDHHMMSSZ.

   .. automethod:: pyasn1.type.useful.GeneralizedTime.clone(self, value=NoValue(), tagSet=TagSet(), subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
   .. automethod:: pyasn1.type.useful.GeneralizedTime.subtype(self, value=NoValue(), implicitTag=TagSet(), explicitTag=TagSet(),subtypeSpec=ConstraintsIntersection(), encoding='us-ascii')
