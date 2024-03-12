.. _api:

Developer Interfaces
====================

.. module:: charset_normalizer

Main Interfaces
---------------

Those functions are publicly exposed and are protected through our BC guarantee.

.. autofunction:: from_bytes
.. autofunction:: from_fp
.. autofunction:: from_path

.. autofunction:: normalize

.. autoclass:: charset_normalizer.CharsetMatches
    :inherited-members:
.. autoclass:: charset_normalizer.CharsetMatch
    :inherited-members:

.. autofunction:: detect

.. autofunction:: charset_normalizer.utils.set_logging_handler


Mess Detector
-------------

.. autofunction:: charset_normalizer.md.mess_ratio

This library allows you to extend the capabilities of the mess detector by extending the
class `MessDetectorPlugin`.

.. autoclass:: charset_normalizer.md.MessDetectorPlugin
    :inherited-members:


.. autofunction:: charset_normalizer.md.is_suspiciously_successive_range


Coherence Detector
------------------

.. autofunction:: charset_normalizer.cd.coherence_ratio


Utilities
---------

Some reusable functions used across the project. We do not guarantee the BC in this area.

.. autofunction:: charset_normalizer.utils.is_accentuated

.. autofunction:: charset_normalizer.utils.remove_accent

.. autofunction:: charset_normalizer.utils.unicode_range

.. autofunction:: charset_normalizer.utils.is_latin

.. autofunction:: charset_normalizer.utils.is_ascii

.. autofunction:: charset_normalizer.utils.is_punctuation

.. autofunction:: charset_normalizer.utils.is_symbol

.. autofunction:: charset_normalizer.utils.is_emoticon

.. autofunction:: charset_normalizer.utils.is_separator

.. autofunction:: charset_normalizer.utils.is_case_variable

.. autofunction:: charset_normalizer.utils.is_private_use_only

.. autofunction:: charset_normalizer.utils.is_cjk

.. autofunction:: charset_normalizer.utils.is_hiragana

.. autofunction:: charset_normalizer.utils.is_katakana

.. autofunction:: charset_normalizer.utils.is_hangul

.. autofunction:: charset_normalizer.utils.is_thai

.. autofunction:: charset_normalizer.utils.is_unicode_range_secondary

.. autofunction:: charset_normalizer.utils.any_specified_encoding

.. autofunction:: charset_normalizer.utils.is_multi_byte_encoding

.. autofunction:: charset_normalizer.utils.identify_sig_or_bom

.. autofunction:: charset_normalizer.utils.should_strip_sig_or_bom

.. autofunction:: charset_normalizer.utils.iana_name

.. autofunction:: charset_normalizer.utils.range_scan

.. autofunction:: charset_normalizer.utils.is_cp_similar
