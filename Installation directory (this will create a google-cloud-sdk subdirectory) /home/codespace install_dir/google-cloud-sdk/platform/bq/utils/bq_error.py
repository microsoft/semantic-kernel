#!/usr/bin/env python
"""Utility functions and classes for BQ CLI errors."""

import textwrap
from typing import Dict, List, Optional

import bq_flags
from utils import bq_logging


P12_DEPRECATION_MESSAGE = (
    'BQ CLI no longer supports the deprecated P12 format by default. To migrate'
    ' to the new JSON service account key format, follow the steps in'
    ' https://cloud.google.com/iam/docs/keys-create-delete#creating. To force'
    ' BQ CLI to recognize P12 keys, re-run the command with'
    ' --nouse_google_auth.'
)


class BigqueryError(Exception):
  """Class to represent a BigQuery error."""


class BigqueryCommunicationError(BigqueryError):
  """Error communicating with the server."""


class BigqueryInterfaceError(BigqueryError):
  """Response from server missing required fields."""


class BigqueryServiceError(BigqueryError):
  """Base class of Bigquery-specific error responses.

  The BigQuery server received request and returned an error.
  """

  def __init__(
      self,
      message: str,
      error: Dict[str, str],
      error_list: List[Dict[str, str]],
      job_ref: Optional[str] = None,
      *args,
      **kwds,
  ):
    # pylint: disable=g-doc-args
    # pylint: disable=keyword-arg-before-vararg
    """Initializes a BigqueryServiceError.

    Args:
      message: A user-facing error message.
      error: The error dictionary, code may inspect the 'reason' key.
      error_list: A list of additional entries, for example a load job may
        contain multiple errors here for each error encountered during
        processing.
      job_ref: Optional JobReference string, if this error was encountered while
        processing a job.
    """
    super().__init__(message, *args, **kwds)
    self.error = error
    self.error_list = error_list
    self.job_ref = job_ref

  def __repr__(self):
    return '%s: error=%s, error_list=%s, job_ref=%s' % (
        self.__class__.__name__,
        self.error,
        self.error_list,
        self.job_ref,
    )


class BigqueryNotFoundError(BigqueryServiceError):
  """The requested resource or identifier was not found."""


class BigqueryDuplicateError(BigqueryServiceError):
  """The requested resource or identifier already exists."""


class BigqueryAccessDeniedError(BigqueryServiceError):
  """The user does not have access to the requested resource."""


class BigqueryInvalidQueryError(BigqueryServiceError):
  """The SQL statement is invalid."""


class BigqueryTermsOfServiceError(BigqueryAccessDeniedError):
  """User has not ACK'd ToS."""


class BigqueryBackendError(BigqueryServiceError):
  """A backend error typically corresponding to retriable HTTP 5xx failures."""


class BigqueryClientError(BigqueryError):
  """Invalid use of BigqueryClient."""


class BigqueryClientConfigurationError(BigqueryClientError):
  """Invalid configuration of BigqueryClient."""


class BigquerySchemaError(BigqueryClientError):
  """Error in locating or parsing the schema."""


class BigqueryTableConstraintsError(BigqueryClientError):
  """Error in locating or parsing the table constraints."""


def CreateBigqueryError(
    error: Dict[str, str],
    server_error: Dict[str, str],
    error_ls: List[Dict[str, str]],
    job_ref: Optional[str] = None,
    session_id: Optional[str] = None,
) -> BigqueryError:
  """Returns a BigqueryError for json error embedded in server_error.

  If error_ls contains any errors other than the given one, those
  are also included in the returned message.

  Args:
    error: The primary error to convert.
    server_error: The error returned by the server. (This is only used in the
      case that error is malformed.)
    error_ls: Additional errors to include in the error message.
    job_ref: String representation a JobReference, if this is an error
      associated with a job.
    session_id: Id of the session if the job is part of one.

  Returns:
    BigqueryError representing error.
  """
  reason = error.get('reason')
  if job_ref:
    message = f"Error processing job '{job_ref}': {error.get('message')}"
  else:
    message = error.get('message', '')
  # We don't want to repeat the "main" error message.
  new_errors = [err for err in error_ls if err != error]
  if new_errors:
    message += '\nFailure details:\n'
  wrap_error_message = True
  new_error_messages = [
      ': '.join(filter(None, [err.get('location'), err.get('message')]))
      for err in new_errors
  ]
  if wrap_error_message:
    message += '\n'.join(
        textwrap.fill(msg, initial_indent=' - ', subsequent_indent='   ')
        for msg in new_error_messages
    )
  else:
    error_message = '\n'.join(new_error_messages)
    if error_message:
      message += '- ' + error_message
  if session_id:
    message += '\nIn session: %s' % session_id

  # Sometimes we will have type(message) being <type 'unicode'>, for example
  # from an invalid query containing a non-English string.  Reduce this
  # to <type 'string'> now -- otherwise it's a trap for any code that
  # tries to %s-format the exception later: str() uses 'ascii' codec.
  # And the message is for display only, so this shouldn't confuse other code.
  message = bq_logging.EncodeForPrinting(message)

  if not reason or not message:
    return BigqueryInterfaceError(
        'Error reported by server with missing error fields. '
        'Server returned: %s' % (str(server_error),)
    )
  if reason == 'notFound':
    return BigqueryNotFoundError(message, error, error_ls, job_ref=job_ref)
  if reason == 'duplicate':
    return BigqueryDuplicateError(message, error, error_ls, job_ref=job_ref)
  if reason == 'accessDenied':
    return BigqueryAccessDeniedError(message, error, error_ls, job_ref=job_ref)
  if reason == 'invalidQuery':
    return BigqueryInvalidQueryError(message, error, error_ls, job_ref=job_ref)
  if reason == 'termsOfServiceNotAccepted':
    return BigqueryTermsOfServiceError(
        message, error, error_ls, job_ref=job_ref
    )
  if reason == 'backendError':
    return BigqueryBackendError(message, error, error_ls, job_ref=job_ref)
  # We map the remaining errors to BigqueryServiceError.
  return BigqueryServiceError(message, error, error_ls, job_ref=job_ref)
