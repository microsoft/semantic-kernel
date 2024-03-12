
ASN.1 library for Python
========================

.. toctree::
   :maxdepth: 1

Abstract Syntax Notation One (`ASN.1
<http://en.wikipedia.org/wiki/Abstract_Syntax_Notation_1x>`_) is a
technology for exchanging structured data in a universally understood,
hardware agnostic way. Many industrial, security and telephony
applications heavily rely on ASN.1.

The `pyasn1 <https://pypi.python.org/pypi/pyasn1/>`_ library implements
ASN.1 support in pure-Python.

What is ASN.1
-------------

ASN.1 is a large, arguably over-engineered and extremely old data modelling and
serialisation tool. It is probably among the first serialisation protocols in
the history of computer science and technology.

ASN.1 started its life over 30 years ago as a serialisation mechanism for the first
electronic mail (known as X.400). Later on if was split off the e-mail application
and become a stand-alone tech still being actively supported by its designers
and widely used in industry and technology.

Since then ASN.1 is sort of haunted by its relations with the OSI model -- the
first, unsuccessful, version of the Internet. You can read many interesting
`discussions <https://news.ycombinator.com/item?id=8871453>`_ on that topic.

In the following years, generations of software engineers tackled the serialisation
problem many times. We can see that in Google's `ProtoBuffers <https://developers.google.com/protocol-buffers/>`_
or `FlatBuffers <https://google.github.io/flatbuffers/>`_, for example.
Interestingly, many new takes on binary protocol design do not depart
far from ASN.1 from technical perspective. It's more of a matter of striking
a balance between processing overhead, wire format overhead and human
readability.

Looking at what ASN.1 has to offer, it has three loosely coupled parts:

* Data types: the standard introduces a collection of basic data types
  (integers, bits, strings, arrays and records) that can be used for describing
  arbitrarily complex, nested data structures.

* Serialisation protocols: the above data structures could be converted into a
  series of octets for storage or transmission over the wire as well as
  recovered back into their structured form. The system is fully agnostic
  to hardware architectures differences.

* Schema language: ASN.1 data structures could be described in terms
  of a schema language for ASN.1 compiler to turn it into platform-specific
  implementation.

ASN.1 applications
------------------

Being an old and generally successful standard, ASN.1 is widely
adopted for many uses. To give you an example, these technologies
use ASN.1 for their data exchange needs:

* Signaling standards for the public switched telephone network (SS7 family)
* Network management standards (SNMP, CMIP)
* Directory standards (X.500 family, LDAP)
* Public Key Infrastructure standards (X.509, etc.)
* PBX control (CSTA)
* IP-based Videoconferencing (H.323 family)
* Biometrics (BIP, CBEFF, ACBio)
* Intelligent transportation (SAE J2735)
* Cellular telephony (GSM, GPRS/EDGE, UMTS, LTE)

ASN.1 gotchas
-------------

Apparently, ASN.1 is hard to implement properly. Quality open-source
ASN.1 tools are rare, but ad-hoc implementations are numerous. Judging from the
`statistics <http://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=ASN.1>`_ on discovered
security vulnerabilities, many people have implemented ASN.1 parsers
and oftentimes fell victim to its edge cases.

On the bright side, ASN.1 has been around for a long time, it is well understood
and security reviewed.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   /pyasn1/contents

Use case
--------

.. toctree::
   :maxdepth: 2

   /example-use-case

Download & Install
------------------

.. toctree::
   :maxdepth: 2

   /download

Changes
-------

All changes and release history is maintained in changelog.  There you
could also download the latest unreleased pyasn1 tarball containing
the latest fixes and improvements.

.. toctree::
   :maxdepth: 1

   /changelog

License
-------

The PyASN1 software is distributed under 2-clause BSD License.

.. toctree::
   :maxdepth: 2

   /license

Getting help
------------

Please, file your `issues <https://github.com/etingof/pyasn1/issues>`_
and `PRs <https://github.com/etingof/pyasn1/pulls>`_ at GitHub.
Alternatively, you could ask for help at
`Stack Overflow <http://stackoverflow.com/questions/tagged/pyasn1>`_
or search
`pyasn1-users <https://lists.sourceforge.net/lists/listinfo/pyasn1-users>`_
mailing list archive.

Books on ASN.1
--------------

The pyasn1 implementation is largely based on reading up the following awesome
books:

* `ASN.1 - Communication between heterogeneous systems <http://www.oss.com/asn1/dubuisson.html>`_ by Olivier Dubuisson
* `ASN.1 Complete <http://www.oss.com/asn1/resources/books-whitepapers-pubs/larmouth-asn1-book.pdf>`_ by Prof John Larmouth

Here you can get the official standards which is hard to read:

* `ITU standards <http://www.itu.int/ITU-T/studygroups/com17/languages/X.680-X.693-0207w.zip>`_

On the other end of the readability spectrum, here is a quick and sweet write up:

* `A Layman's Guide to a Subset of ASN.1, BER, and DER <ftp://ftp.rsasecurity.com/pub/pkcs/ascii/layman.asc>`_ by Burton S. Kaliski

If you are working with ASN.1, we'd highly recommend reading a proper
book on the subject.

