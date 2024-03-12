Command Line Interface
======================

charset-normalizer ship with a CLI that should be available as `normalizer`.
This is a great tool to fully exploit the detector capabilities without having to write Python code.

Possible use cases:
#. Quickly discover probable originating charset from a file.
#. I want to quickly convert a non Unicode file to Unicode.
#. Debug the charset-detector.

Down bellow, we will guide you through some basic examples.

Arguments
---------

You may simply invoke `normalizer -h` (with the h(elp) flag) to understand the basics.

::

   usage: normalizer [-h] [-v] [-a] [-n] [-m] [-r] [-f] [-t THRESHOLD]
                     file [file ...]

   The Real First Universal Charset Detector. Discover originating encoding used
   on text file. Normalize text to unicode.

   positional arguments:
     files                 File(s) to be analysed

   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         Display complementary information about file if any.
                           Stdout will contain logs about the detection process.
     -a, --with-alternative
                           Output complementary possibilities if any. Top-level
                           JSON WILL be a list.
     -n, --normalize       Permit to normalize input file. If not set, program
                           does not write anything.
     -m, --minimal         Only output the charset detected to STDOUT. Disabling
                           JSON output.
     -r, --replace         Replace file when trying to normalize it instead of
                           creating a new one.
     -f, --force           Replace file without asking if you are sure, use this
                           flag with caution.
     -t THRESHOLD, --threshold THRESHOLD
                           Define a custom maximum amount of chaos allowed in
                           decoded content. 0. <= chaos <= 1.
     --version             Show version information and exit.

.. code:: bash

   normalizer ./data/sample.1.fr.srt

Main JSON Output
----------------

🎉 Since version 1.4.0 the CLI produce easily usable stdout result in
JSON format.

.. code:: json

   {
       "path": "/home/default/projects/charset_normalizer/data/sample.1.fr.srt",
       "encoding": "cp1252",
       "encoding_aliases": [
           "1252",
           "windows_1252"
       ],
       "alternative_encodings": [
           "cp1254",
           "cp1256",
           "cp1258",
           "iso8859_14",
           "iso8859_15",
           "iso8859_16",
           "iso8859_3",
           "iso8859_9",
           "latin_1",
           "mbcs"
       ],
       "language": "French",
       "alphabets": [
           "Basic Latin",
           "Latin-1 Supplement"
       ],
       "has_sig_or_bom": false,
       "chaos": 0.149,
       "coherence": 97.152,
       "unicode_path": null,
       "is_preferred": true
   }


I recommend the `jq` command line tool to easily parse and exploit specific data from the produced JSON.

Multiple File Input
-------------------

It is possible to give multiple files to the CLI. It will produce a list instead of an object at the top level.
When using the `-m` (minimal output) it will rather print one result (encoding) per line.

Unicode Conversion
------------------

If you desire to convert any file to Unicode you will need to append the flag `-n`. It will produce another file,
it won't replace it by default.

The newly created file path will be declared in `unicode_path` (JSON output).
