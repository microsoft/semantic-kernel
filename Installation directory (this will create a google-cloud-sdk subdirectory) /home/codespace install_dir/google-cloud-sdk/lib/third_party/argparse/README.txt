The argparse module makes it easy to write user friendly command line
interfaces.

The program defines what arguments it requires, and argparse will figure out
how to parse those out of sys.argv. The argparse module also automatically
generates help and usage messages and issues errors when users give the
program invalid arguments.

As of Python >= 2.7 and >= 3.2, the argparse module is maintained within the
Python standard library. For users who still need to support Python < 2.7 or
< 3.2, it is also provided as a separate package, which tries to stay
compatible with the module in the standard library, but also supports older
Python versions.

argparse is licensed under the Python license, for details see LICENSE.txt.


Compatibility
-------------

argparse should work on Python >= 2.3, it was tested on:

* 2.3.5, 2.4.4, 2.5.5, 2.6.5 and 2.7
* 3.1, 3.2


Installation
------------

Try one of these:

    python setup.py install

    easy_install argparse

    pip install argparse

    putting argparse.py in some directory listed in sys.path should also work


Bugs
----

If you find a bug, please try to reproduce it with python 2.7.

If it happens there also, please file a bug in the python.org issue tracker.
If it does not happen in 2.7, file a bug in the argparse package issue tracker.

