#!/usr/bin/env python
"""Utility functions for BQ CLI logging."""

import logging
import sys
from typing import Optional, TextIO

from absl import flags
from absl import logging as absl_logging
from googleapiclient import model


def ConfigurePythonLogger(apilog: Optional[str] = None):
  """Sets up Python logger.

  Applications can configure logging however they want, but this
  captures one pattern of logging which seems useful when dealing with
  a single command line option for determining logging.

  Args:
    apilog: To log to sys.stdout, specify '', '-', '1', 'true', or 'stdout'. To
      log to sys.stderr, specify 'stderr'. To log to a file, specify the file
      path. Specify None to disable logging.
  """
  if apilog is None:
    # Effectively turn off logging.
    logging.debug(
        'There is no apilog flag so non-critical logging is disabled.'
    )
    logging.disable(logging.CRITICAL)
  else:
    if apilog in ('', '-', '1', 'true', 'stdout'):
      _SetLogFile(sys.stdout)
    elif apilog == 'stderr':
      _SetLogFile(sys.stderr)
    elif apilog:
      _SetLogFile(open(apilog, 'w'))
    else:
      logging.basicConfig(level=logging.INFO)
    # Turn on apiclient logging of http requests and responses. (Here
    # we handle both the flags interface from apiclient < 1.2 and the
    # module global in apiclient >= 1.2.)
    if hasattr(flags.FLAGS, 'dump_request_response'):
      flags.FLAGS.dump_request_response = True
    else:
      model.dump_request_response = True


def _SetLogFile(logfile: TextIO):
  absl_logging.use_python_logging(quiet=True)
  absl_logging.get_absl_handler().python_handler.stream = logfile


def EncodeForPrinting(o: object) -> str:
  """Safely encode an object as the encoding for sys.stdout."""
  # Not all file objects provide an encoding attribute, so we make sure to
  # handle the case where the attribute is completely absent.
  encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
  # We want to prevent conflicts in python2 between formatting
  # a str type with a unicode type, e.g. b'abc%s' % (u'[unicode]',)
  # where the byte type will be auto decoded as ascii thus causing
  # an error.
  # Thus we only want to encode the object if it's passed in as a
  # unicode type and the unicode type is not a str type.
  if isinstance(o, type('')) and not isinstance(o, str):
    return o.encode(encoding, 'backslashreplace')
  else:
    return str(o)
