#!/usr/bin/env python
# Copyright (c) 2006-2011 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from __future__ import print_function

import argparse
import os
import sys

from nose.core import run


def main():
    description = ("Runs boto unit and/or integration tests. "
                   "Arguments will be passed on to nosetests. "
                   "See nosetests --help for more information.")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-t', '--service-tests', action="append", default=[],
                        help="Run tests for a given service.  This will "
                        "run any test tagged with the specified value, "
                        "e.g -t s3 -t ec2")
    known_args, remaining_args = parser.parse_known_args()
    attribute_args = []
    for service_attribute in known_args.service_tests:
        attribute_args.extend(['-a', '!notdefault,' + service_attribute])
    if not attribute_args:
        # If the user did not specify any filtering criteria, we at least
        # will filter out any test tagged 'notdefault'.
        attribute_args = ['-a', '!notdefault']

    # Set default tests used by e.g. tox. For Py2 this means all unit
    # tests, while for Py3 it's just whitelisted ones.
    if 'default' in remaining_args:
        # Run from the base project directory
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        for i, arg in enumerate(remaining_args):
            if arg == 'default':
                remaining_args[i] = 'tests/unit'

    all_args = [__file__] + attribute_args + remaining_args
    print("nose command:", ' '.join(all_args))
    if run(argv=all_args):
        # run will return True is all the tests pass.  We want
        # this to equal a 0 rc
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
