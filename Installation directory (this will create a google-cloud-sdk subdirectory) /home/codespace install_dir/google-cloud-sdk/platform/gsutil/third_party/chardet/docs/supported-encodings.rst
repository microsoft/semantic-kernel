Supported encodings
===================

Universal Encoding Detector currently supports over two dozen character
encodings.

-  ``Big5``, ``GB2312``/``GB18030``, ``EUC-TW``, ``HZ-GB-2312``, and
   ``ISO-2022-CN`` (Traditional and Simplified Chinese)
-  ``EUC-JP``, ``SHIFT_JIS``, and ``ISO-2022-JP`` (Japanese)
-  ``EUC-KR`` and ``ISO-2022-KR`` (Korean)
-  ``KOI8-R``, ``MacCyrillic``, ``IBM855``, ``IBM866``, ``ISO-8859-5``,
   and ``windows-1251`` (Russian)
-  ``ISO-8859-2`` and ``windows-1250`` (Hungarian)
-  ``ISO-8859-5`` and ``windows-1251`` (Bulgarian)
-  ``ISO-8859-1`` and ``windows-1252`` (Western European languages)
-  ``ISO-8859-7`` and ``windows-1253`` (Greek)
-  ``ISO-8859-8`` and ``windows-1255`` (Visual and Logical Hebrew)
-  ``TIS-620`` (Thai)
-  ``UTF-32`` BE, LE, 3412-ordered, or 2143-ordered (with a BOM)
-  ``UTF-16`` BE or LE (with a BOM)
-  ``UTF-8`` (with or without a BOM)
-  ASCII

.. warning::

    Due to inherent similarities between certain encodings, some encodings may
    be detected incorrectly. In my tests, the most problematic case was
    Hungarian text encoded as ``ISO-8859-2`` or ``windows-1250`` (encoded as
    one but reported as the other). Also, Greek text encoded as ``ISO-8859-7``
    was often mis-reported as ``ISO-8859-2``. Your mileage may vary.
