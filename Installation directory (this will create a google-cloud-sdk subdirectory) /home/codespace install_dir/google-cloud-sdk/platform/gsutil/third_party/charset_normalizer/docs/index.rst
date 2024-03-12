===================
 Charset Normalizer
===================

Overview
========

A Library that helps you read text from unknown charset encoding.
This project is motivated by chardet, I'm trying to resolve the issue by taking another approach.
All IANA character set names for which the Python core library provides codecs are supported.

It aims to be as generic as possible.

.. image:: https://repository-images.githubusercontent.com/200259335/d3da9600-dedc-11e9-83e8-081f597505df
   :width: 500px
   :scale: 100 %
   :alt: CLI Charset Normalizer
   :align: right


It is released under MIT license, see LICENSE for more
details. Be aware that no warranty of any kind is provided with this package.

Copyright (C) 2019 Ahmed TAHRI @Ousret <ahmed(dot)tahri(at)cloudnursery.dev>

Introduction
============

This library aim to assist you in finding what encoding suit the best to content.
It **DOES NOT** try to uncover the originating encoding, in fact this program does not care about it.

By originating we means the one that was precisely used to encode a text file.

Precisely ::

    my_byte_str = 'Bonjour, je suis à la recherche d\'une aide sur les étoiles'.encode('cp1252')


We **ARE NOT** looking for cp1252 **BUT FOR** ``Bonjour, je suis à la recherche d'une aide sur les étoiles``.
Because of this ::

    my_byte_str.decode('cp1252') == my_byte_str.decode('cp1256') == my_byte_str.decode('cp1258') == my_byte_str.decode('iso8859_14')
    # Print True !

There is no wrong answer to decode ``my_byte_str`` to get the exact same result.
This is where this library differ from others. There's not specific probe per encoding table.

Features
========

- Encoding detection on a fp (file pointer), bytes or PathLike.
- Transpose any encoded content to Unicode the best we can.
- Detect spoken language in text.
- Ship with a great CLI.

Start Guide
-----------

.. toctree::
    :maxdepth: 2

    user/support
    user/getstarted
    user/advanced_search
    user/handling_result
    user/miscellaneous
    user/cli

Community Guide
---------------

.. toctree::
    :maxdepth: 2

    community/faq
    community/why_migrate

Developer Guide
---------------

.. toctree::
    :maxdepth: 3

    api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
