Usage
=====

Basic usage
-----------

The easiest way to use the Universal Encoding Detector library is with
the ``detect`` function.


Example: Using the ``detect`` function
--------------------------------------

The ``detect`` function takes one argument, a non-Unicode string. It
returns a dictionary containing the auto-detected character encoding and
a confidence level from ``0`` to ``1``.

.. code:: python

    >>> import urllib
    >>> rawdata = urllib.urlopen('http://yahoo.co.jp/').read()
    >>> import chardet
    >>> chardet.detect(rawdata)
    {'encoding': 'EUC-JP', 'confidence': 0.99}

Advanced usage
--------------

If you’re dealing with a large amount of text, you can call the
Universal Encoding Detector library incrementally, and it will stop as
soon as it is confident enough to report its results.

Create a ``UniversalDetector`` object, then call its ``feed`` method
repeatedly with each block of text. If the detector reaches a minimum
threshold of confidence, it will set ``detector.done`` to ``True``.

Once you’ve exhausted the source text, call ``detector.close()``, which
will do some final calculations in case the detector didn’t hit its
minimum confidence threshold earlier. Then ``detector.result`` will be a
dictionary containing the auto-detected character encoding and
confidence level (the same as the ``chardet.detect`` function 
`returns <usage.html#example-using-the-detect-function>`__).


Example: Detecting encoding incrementally
-----------------------------------------

.. code:: python

    import urllib
    from chardet.universaldetector import UniversalDetector

    usock = urllib.urlopen('http://yahoo.co.jp/')
    detector = UniversalDetector()
    for line in usock.readlines():
        detector.feed(line)
        if detector.done: break
    detector.close()
    usock.close()
    print detector.result

.. code:: python

    {'encoding': 'EUC-JP', 'confidence': 0.99}

If you want to detect the encoding of multiple texts (such as separate
files), you can re-use a single ``UniversalDetector`` object. Just call
``detector.reset()`` at the start of each file, call ``detector.feed``
as many times as you like, and then call ``detector.close()`` and check
the ``detector.result`` dictionary for the file’s results.

Example: Detecting encodings of multiple files
----------------------------------------------

.. code:: python

    import glob
    from chardet.universaldetector import UniversalDetector

    detector = UniversalDetector()
    for filename in glob.glob('*.xml'):
        print filename.ljust(60),
        detector.reset()
        for line in file(filename, 'rb'):
            detector.feed(line)
            if detector.done: break
        detector.close()
        print detector.result
