==============
 Miscellaneous
==============

Convert to str
--------------

Any ``CharsetMatch`` object can be transformed to exploitable ``str`` variable.

 ::

    my_byte_str = '我没有埋怨，磋砣的只是一些时间。'.encode('gb18030')

    # Assign return value so we can fully exploit result
    result = from_bytes(
        my_byte_str
    ).best()

    # This should print '我没有埋怨，磋砣的只是一些时间。'
    print(str(result))


Logging
-------

Prior to the version 2.0.10 you may encounter some unexpected logs in your streams.
Something along the line of:

 ::

    ... | WARNING | override steps (5) and chunk_size (512) as content does not fit (465 byte(s) given) parameters.
    ... | INFO | ascii passed initial chaos probing. Mean measured chaos is 0.000000 %
    ... | INFO | ascii should target any language(s) of ['Latin Based']


It is most likely because you altered the root getLogger instance. The package has its own logic behind logging and why
it is useful. See https://docs.python.org/3/howto/logging.html to learn the basics.

If you are looking to silence and/or reduce drastically the amount of logs, please upgrade to the latest version
available for `charset-normalizer` using your package manager or by `pip install charset-normalizer -U`.

The latest version will no longer produce any entry greater than `DEBUG`.
On `DEBUG` only one entry will be observed and that is about the detection result.

Then regarding the others log entries, they will be pushed as `Level 5`. Commonly known as TRACE level, but we do
not register it globally.
