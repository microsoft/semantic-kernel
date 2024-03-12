import sys

# use unittest2 under Python 2.6 and earlier.
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest
