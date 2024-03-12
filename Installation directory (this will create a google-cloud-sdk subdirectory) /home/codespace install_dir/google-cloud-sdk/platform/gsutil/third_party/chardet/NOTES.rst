Class Hierarchy for chardet
===========================

Universal Detector
------------------
Has a list of probers.

CharSetProber
-------------
Mostly abstract parent class.

CharSetGroupProber
------------------
Runs a bunch of related probers at the same time and decides which is best.

SBCSGroupProber
---------------
SBCS = Single-ByteCharSet. Runs a bunch of SingleByteCharSetProbers.  Always
contains the same SingleByteCharSetProbers.

SingleByteCharSetProber
-----------------------
A CharSetProber that is used for detecting single-byte encodings by using
a "precedence matrix" (i.e., a character bigram model).

MBCSGroupProber
---------------
Runs a bunch of MultiByteCharSetProbers. It also uses a UTF8Prober, which is
essentially a MultiByteCharSetProber that only has a state machine.  Always
contains the same MultiByteCharSetProbers.

MultiByteCharSetProber
----------------------
A CharSetProber that uses both a character unigram model (or "character
distribution analysis") and an independent state machine for trying to
detect and encoding.

CodingStateMachine
------------------
Used for "coding scheme" detection, where we just look for either invalid
byte sequences or sequences that only occur for that particular encoding.

CharDistributionAnalysis
------------------------
Used for character unigram distribution encoding detection.  Takes a mapping
from characters to a "frequency order" (i.e., what frequency rank that byte has
in the given encoding) and a "typical distribution ratio", which is the number
of occurrences of the 512 most frequently used characters divided by the number
of occurrences of the rest of the characters for a typical document.
The "characters" in this case are 2-byte sequences and they are first converted
to an "order" (name comes from ord() function, I believe). This "order" is used
to index into the frequency order table to determine the frequency rank of that
byte sequence.  The reason this extra step is necessary is that the frequency
rank table is language-specific (and not encoding-specific).


What's where
============


Bigram files
------------

- ``hebrewprober.py``
- ``jpcntxprober.py``
- ``langbulgarianmodel.py``
- ``langcyrillicmodel.py``
- ``langgreekmodel.py``
- ``langhebrewmodel.py``
- ``langhungarianmodel.py``
- ``langthaimodel.py``
- ``latin1prober.py``
- ``sbcharsetprober.py``
- ``sbcsgroupprober.py``


Coding Scheme files
-------------------

- ``escprober.py``
- ``escsm.py``
- ``utf8prober.py``
- ``codingstatemachine.py``
- ``mbcssmprober.py``


Unigram files
-------------

- ``big5freqprober.py``
- ``chardistribution.py``
- ``euckrfreqprober.py``
- ``euctwfreqprober.py``
- ``gb2312freqprober.py``
- ``jisfreqprober.py``

Multibyte probers
-----------------

- ``big5prober.py``
- ``cp949prober.py``
- ``eucjpprober.py``
- ``euckrprober.py``
- ``euctwprober.py``
- ``gb2312prober.py``
- ``mbcharsetprober.py``
- ``mbcsgroupprober.py``
- ``sjisprober.py``

Misc files
----------

- ``__init__.py`` (currently has ``detect`` function in it)
- ``compat.py``
- ``enums.py``
- ``universaldetector.py``
- ``version.py``


Useful links
============

This is just a collection of information that I've found useful or thought
might be useful in the future:

- `BOM by Encoding`_

- `A Composite Approach to Language/Encoding Detection`_

- `What Every Programmer Absolutely...`_

- The actual `source`_


.. _BOM by Encoding:
    https://en.wikipedia.org/wiki/Byte_order_mark#Representations_of_byte_order_marks_by_encoding
.. _A Composite Approach to Language/Encoding Detection:
    http://www-archive.mozilla.org/projects/intl/UniversalCharsetDetection.html
.. _What Every Programmer Absolutely...: http://kunststube.net/encoding/
.. _source: https://mxr.mozilla.org/mozilla/source/intl/chardet/
