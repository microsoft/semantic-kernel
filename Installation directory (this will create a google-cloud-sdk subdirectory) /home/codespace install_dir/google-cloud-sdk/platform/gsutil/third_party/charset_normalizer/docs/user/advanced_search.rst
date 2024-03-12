Advanced Search
===============

Charset Normalizer method ``from_bytes``, ``from_fp`` and ``from_path`` provide some
optional parameters that can be tweaked.

As follow ::

    from charset_normalizer import from_bytes

    my_byte_str = '我没有埋怨，磋砣的只是一些时间。'.encode('gb18030')

    results = from_bytes(
        my_byte_str,
        steps=10,  # Number of steps/block to extract from my_byte_str
        chunk_size=512,  # Set block size of each extraction
        threshold=0.2,  # Maximum amount of chaos allowed on first pass
        cp_isolation=None,  # Finite list of encoding to use when searching for a match
        cp_exclusion=None,  # Finite list of encoding to avoid when searching for a match
        preemptive_behaviour=True,  # Determine if we should look into my_byte_str (ASCII-Mode) for pre-defined encoding
        explain=False  # Print on screen what is happening when searching for a match
    )


Using CharsetMatches
------------------------------

Here, ``results`` is a ``CharsetMatches`` object. It behave like a list but does not implements all related methods.
Initially, it is sorted. Calling ``best()`` is sufficient to extract the most probable result.

.. autoclass:: charset_normalizer.CharsetMatches
    :members:

List behaviour
--------------

Like said earlier, ``CharsetMatches`` object behave like a list.

  ::

    # Call len on results also work
    if not results:
        print('No match for your sequence')

    # Iterate over results like a list
    for match in results:
        print(match.encoding, 'can decode properly your sequence using', match.alphabets, 'and language', match.language)

    # Using index to access results
    if results:
        print(str(results[0]))

Using best()
------------

Like said above, ``CharsetMatches`` object behave like a list and it is sorted by default after getting results from
``from_bytes``, ``from_fp`` or ``from_path``.

Using ``best()`` return the most probable result, the first entry of the list. Eg. idx 0.
It return a ``CharsetMatch`` object as return value or None if there is not results inside it.

 ::

    result = results.best()

Calling first()
---------------

The very same thing than calling the method ``best()``.

Class aliases
-------------

``CharsetMatches`` is also known as ``CharsetDetector``, ``CharsetDoctor`` and ``CharsetNormalizerMatches``.
It is useful if you prefer short class name.

Verbose output
--------------

You may want to understand why a specific encoding was not picked by charset_normalizer. All you have to do is passing
``explain`` to True when using methods ``from_bytes``, ``from_fp`` or ``from_path``.
