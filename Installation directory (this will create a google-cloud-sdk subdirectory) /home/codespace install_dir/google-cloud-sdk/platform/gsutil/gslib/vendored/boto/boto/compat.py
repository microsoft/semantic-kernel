# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#
import os

# This allows boto modules to say "from boto.compat import json".  This is
# preferred so that all modules don't have to repeat this idiom.
try:
    import simplejson as json
except ImportError:
    import json


# Switch to use encodebytes, which deprecates encodestring in Python 3
try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


# If running in Google App Engine there is no "user" and
# os.path.expanduser() will fail. Attempt to detect this case and use a
# no-op expanduser function in this case.
try:
    os.path.expanduser('~')
    expanduser = os.path.expanduser
except (AttributeError, ImportError):
    # This is probably running on App Engine.
    expanduser = (lambda x: x)

from boto.vendored import six
import http.client as http_client
from io import BytesIO, StringIO
import urllib
import _thread
from queue import Queue
from urllib.parse import parse_qs, quote, unquote, urlparse, urlsplit
from urllib.parse import unquote_plus
from urllib.request import urlopen

# StandardError was removed, so use the base exception type instead
StandardError = Exception
long_type = int
from configparser import ConfigParser, NoOptionError, NoSectionError
unquote_str = unquote_plus
parse_qs_safe = parse_qs
