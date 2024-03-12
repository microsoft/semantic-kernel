# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# All rights reserved.
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

"""
Exception classes - Subclassing allows you to check for specific errors
"""
import base64
import xml.sax

import boto

from boto import handler
from boto.compat import json, StandardError
from boto.resultset import ResultSet


class BotoClientError(StandardError):
    """
    General Boto Client error (error accessing AWS)
    """
    def __init__(self, reason, *args):
        super(BotoClientError, self).__init__(reason, *args)
        self.reason = reason

    def __repr__(self):
        return 'BotoClientError: %s' % self.reason

    def __str__(self):
        return 'BotoClientError: %s' % self.reason


class SDBPersistenceError(StandardError):
    pass


class StoragePermissionsError(BotoClientError):
    """
    Permissions error when accessing a bucket or key on a storage service.
    """
    pass


class S3PermissionsError(StoragePermissionsError):
    """
    Permissions error when accessing a bucket or key on S3.
    """
    pass


class GSPermissionsError(StoragePermissionsError):
    """
    Permissions error when accessing a bucket or key on GS.
    """
    pass


class BotoServerError(StandardError):
    def __init__(self, status, reason, body=None, *args):
        super(BotoServerError, self).__init__(status, reason, body, *args)
        self.status = status
        self.reason = reason
        self.body = body or ''
        self.request_id = None
        self.error_code = None
        self._error_message = None
        self.message = ''
        self.box_usage = None

        if isinstance(self.body, bytes):
            try:
                self.body = self.body.decode('utf-8')
            except UnicodeDecodeError:
                boto.log.debug('Unable to decode body from bytes!')

        # Attempt to parse the error response. If body isn't present,
        # then just ignore the error response.
        if self.body:
            # Check if it looks like a ``dict``.
            if hasattr(self.body, 'items'):
                # It's not a string, so trying to parse it will fail.
                # But since it's data, we can work with that.
                self.request_id = self.body.get('RequestId', None)

                if 'Error' in self.body:
                    # XML-style
                    error = self.body.get('Error', {})
                    self.error_code = error.get('Code', None)
                    self.message = error.get('Message', None)
                else:
                    # JSON-style.
                    self.message = self.body.get('message', None)
            else:
                try:
                    h = handler.XmlHandlerWrapper(self, self)
                    h.parseString(self.body)
                except (TypeError, xml.sax.SAXParseException):
                    # What if it's JSON? Let's try that.
                    try:
                        parsed = json.loads(self.body)

                        if 'RequestId' in parsed:
                            self.request_id = parsed['RequestId']
                        if 'Error' in parsed:
                            if 'Code' in parsed['Error']:
                                self.error_code = parsed['Error']['Code']
                            if 'Message' in parsed['Error']:
                                self.message = parsed['Error']['Message']

                    except (TypeError, ValueError):
                        # Remove unparsable message body so we don't include garbage
                        # in exception. But first, save self.body in self.error_message
                        # because occasionally we get error messages from Eucalyptus
                        # that are just text strings that we want to preserve.
                        self.message = self.body
                        self.body = None

    def __getattr__(self, name):
        if name == 'error_message':
            return self.message
        if name == 'code':
            return self.error_code
        raise AttributeError

    def __setattr__(self, name, value):
        if name == 'error_message':
            self.message = value
        else:
            super(BotoServerError, self).__setattr__(name, value)

    def __repr__(self):
        return '%s: %s %s\n%s' % (self.__class__.__name__,
                                  self.status, self.reason, self.body)

    def __str__(self):
        return '%s: %s %s\n%s' % (self.__class__.__name__,
                                  self.status, self.reason, self.body)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name in ('RequestId', 'RequestID'):
            self.request_id = value
        elif name == 'Code':
            self.error_code = value
        elif name == 'Message':
            self.message = value
        elif name == 'BoxUsage':
            self.box_usage = value
        return None

    def _cleanupParsedProperties(self):
        self.request_id = None
        self.error_code = None
        self.message = None
        self.box_usage = None


class ConsoleOutput(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.instance_id = None
        self.timestamp = None
        self.comment = None
        self.output = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'instanceId':
            self.instance_id = value
        elif name == 'output':
            self.output = base64.b64decode(value)
        else:
            setattr(self, name, value)


class StorageCreateError(BotoServerError):
    """
    Error creating a bucket or key on a storage service.
    """
    def __init__(self, status, reason, body=None):
        self.bucket = None
        super(StorageCreateError, self).__init__(status, reason, body)

    def endElement(self, name, value, connection):
        if name == 'BucketName':
            self.bucket = value
        else:
            return super(StorageCreateError, self).endElement(name, value, connection)


class S3CreateError(StorageCreateError):
    """
    Error creating a bucket or key on S3.
    """
    pass


class GSCreateError(StorageCreateError):
    """
    Error creating a bucket or key on GS.
    """
    pass


class StorageCopyError(BotoServerError):
    """
    Error copying a key on a storage service.
    """
    pass


class S3CopyError(StorageCopyError):
    """
    Error copying a key on S3.
    """
    pass


class GSCopyError(StorageCopyError):
    """
    Error copying a key on GS.
    """
    pass


class SQSError(BotoServerError):
    """
    General Error on Simple Queue Service.
    """
    def __init__(self, status, reason, body=None):
        self.detail = None
        self.type = None
        super(SQSError, self).__init__(status, reason, body)

    def startElement(self, name, attrs, connection):
        return super(SQSError, self).startElement(name, attrs, connection)

    def endElement(self, name, value, connection):
        if name == 'Detail':
            self.detail = value
        elif name == 'Type':
            self.type = value
        else:
            return super(SQSError, self).endElement(name, value, connection)

    def _cleanupParsedProperties(self):
        super(SQSError, self)._cleanupParsedProperties()
        for p in ('detail', 'type'):
            setattr(self, p, None)


class SQSDecodeError(BotoClientError):
    """
    Error when decoding an SQS message.
    """
    def __init__(self, reason, message):
        super(SQSDecodeError, self).__init__(reason, message)
        self.message = message

    def __repr__(self):
        return 'SQSDecodeError: %s' % self.reason

    def __str__(self):
        return 'SQSDecodeError: %s' % self.reason


class StorageResponseError(BotoServerError):
    """
    Error in response from a storage service.
    """
    def __init__(self, status, reason, body=None):
        self.resource = None
        super(StorageResponseError, self).__init__(status, reason, body)

    def startElement(self, name, attrs, connection):
        return super(StorageResponseError, self).startElement(
            name, attrs, connection)

    def endElement(self, name, value, connection):
        if name == 'Resource':
            self.resource = value
        else:
            return super(StorageResponseError, self).endElement(
                name, value, connection)

    def _cleanupParsedProperties(self):
        super(StorageResponseError, self)._cleanupParsedProperties()
        for p in ('resource'):
            setattr(self, p, None)


class S3ResponseError(StorageResponseError):
    """
    Error in response from S3.
    """
    def __init__(self, status, reason, body=None):
        self.region = None
        self.endpoint = None
        super(StorageResponseError, self).__init__(status, reason, body)

    def startElement(self, name, attrs, connection):
        return super(StorageResponseError, self).startElement(
            name, attrs, connection)

    def endElement(self, name, value, connection):
        if name == 'Region':
            self.region = value
        elif name == 'LocationConstraint':
            self.region = value
        elif name == 'Endpoint':
            self.endpoint = value
        else:
            return super(StorageResponseError, self).endElement(
                name, value, connection)

    def _cleanupParsedProperties(self):
        super(StorageResponseError, self)._cleanupParsedProperties()
        for p in ('region', 'endpoint'):
            setattr(self, p, None)


class GSResponseError(StorageResponseError):
    """
    Error in response from GS.
    """
    pass


class EC2ResponseError(BotoServerError):
    """
    Error in response from EC2.
    """
    def __init__(self, status, reason, body=None):
        self.errors = None
        self._errorResultSet = []
        super(EC2ResponseError, self).__init__(status, reason, body)
        self.errors = [
            (e.error_code, e.error_message) for e in self._errorResultSet]
        if len(self.errors):
            self.error_code, self.error_message = self.errors[0]

    def startElement(self, name, attrs, connection):
        if name == 'Errors':
            self._errorResultSet = ResultSet([('Error', _EC2Error)])
            return self._errorResultSet
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'RequestID':
            self.request_id = value
        else:
            return None  # don't call subclass here

    def _cleanupParsedProperties(self):
        super(EC2ResponseError, self)._cleanupParsedProperties()
        self._errorResultSet = []
        for p in ('errors'):
            setattr(self, p, None)


class JSONResponseError(BotoServerError):
    """
    This exception expects the fully parsed and decoded JSON response
    body to be passed as the body parameter.

    :ivar status: The HTTP status code.
    :ivar reason: The HTTP reason message.
    :ivar body: The Python dict that represents the decoded JSON
        response body.
    :ivar error_message: The full description of the AWS error encountered.
    :ivar error_code: A short string that identifies the AWS error
        (e.g. ConditionalCheckFailedException)
    """
    def __init__(self, status, reason, body=None, *args):
        self.status = status
        self.reason = reason
        self.body = body
        if self.body:
            self.error_message = self.body.get('message', None)
            self.error_code = self.body.get('__type', None)
            if self.error_code:
                self.error_code = self.error_code.split('#')[-1]


class DynamoDBResponseError(JSONResponseError):
    pass


class SWFResponseError(JSONResponseError):
    pass


class EmrResponseError(BotoServerError):
    """
    Error in response from EMR
    """
    pass


class _EC2Error(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.error_code = None
        self.error_message = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Code':
            self.error_code = value
        elif name == 'Message':
            self.error_message = value
        else:
            return None


class SDBResponseError(BotoServerError):
    """
    Error in responses from SDB.
    """
    pass


class AWSConnectionError(BotoClientError):
    """
    General error connecting to Amazon Web Services.
    """
    pass


class StorageDataError(BotoClientError):
    """
    Error receiving data from a storage service.
    """
    pass


class S3DataError(StorageDataError):
    """
    Error receiving data from S3.
    """
    pass


class GSDataError(StorageDataError):
    """
    Error receiving data from GS.
    """
    pass


class InvalidUriError(Exception):
    """Exception raised when URI is invalid."""

    def __init__(self, message):
        super(InvalidUriError, self).__init__(message)
        self.message = message


class InvalidAclError(Exception):
    """Exception raised when ACL XML is invalid."""

    def __init__(self, message):
        super(InvalidAclError, self).__init__(message)
        self.message = message


class InvalidCorsError(Exception):
    """Exception raised when CORS XML is invalid."""

    def __init__(self, message):
        super(InvalidCorsError, self).__init__(message)
        self.message = message


class InvalidEncryptionConfigError(Exception):
    """Exception raised when GCS encryption configuration XML is invalid."""

    def __init__(self, message):
        super(InvalidEncryptionConfigError, self).__init__(message)
        self.message = message


class InvalidLifecycleConfigError(Exception):
    """Exception raised when GCS lifecycle configuration XML is invalid."""

    def __init__(self, message):
        super(InvalidLifecycleConfigError, self).__init__(message)
        self.message = message


class NoAuthHandlerFound(Exception):
    """Is raised when no auth handlers were found ready to authenticate."""
    pass


# Enum class for resumable upload failure disposition.
class ResumableTransferDisposition(object):
    # START_OVER means an attempt to resume an existing transfer failed,
    # and a new resumable upload should be attempted (without delay).
    START_OVER = 'START_OVER'

    # WAIT_BEFORE_RETRY means the resumable transfer failed but that it can
    # be retried after a time delay within the current process.
    WAIT_BEFORE_RETRY = 'WAIT_BEFORE_RETRY'

    # ABORT_CUR_PROCESS means the resumable transfer failed and that
    # delaying/retrying within the current process will not help. If
    # resumable transfer included a state tracker file the upload can be
    # retried again later, in another process (e.g., a later run of gsutil).
    ABORT_CUR_PROCESS = 'ABORT_CUR_PROCESS'

    # ABORT means the resumable transfer failed in a way that it does not
    # make sense to continue in the current process, and further that the
    # current tracker ID should not be preserved (in a tracker file if one
    # was specified at resumable upload start time). If the user tries again
    # later (e.g., a separate run of gsutil) it will get a new resumable
    # upload ID.
    ABORT = 'ABORT'


class ResumableUploadException(Exception):
    """
    Exception raised for various resumable upload problems.

    self.disposition is of type ResumableTransferDisposition.
    """

    def __init__(self, message, disposition):
        super(ResumableUploadException, self).__init__(message, disposition)
        self.message = message
        self.disposition = disposition

    def __repr__(self):
        return 'ResumableUploadException("%s", %s)' % (
            self.message, self.disposition)


class ResumableDownloadException(Exception):
    """
    Exception raised for various resumable download problems.

    self.disposition is of type ResumableTransferDisposition.
    """

    def __init__(self, message, disposition):
        super(ResumableDownloadException, self).__init__(message, disposition)
        self.message = message
        self.disposition = disposition

    def __repr__(self):
        return 'ResumableDownloadException("%s", %s)' % (
            self.message, self.disposition)


class TooManyRecordsException(Exception):
    """
    Exception raised when a search of Route53 records returns more
    records than requested.
    """

    def __init__(self, message):
        super(TooManyRecordsException, self).__init__(message)
        self.message = message


class PleaseRetryException(Exception):
    """
    Indicates a request should be retried.
    """
    def __init__(self, message, response=None):
        self.message = message
        self.response = response

    def __repr__(self):
        return 'PleaseRetryException("%s", %s)' % (
            self.message,
            self.response
        )


class InvalidInstanceMetadataError(Exception):
    MSG = (
        "You can set the 'metadata_service_num_attempts' "
        "in your boto config file to increase the number "
        "of times boto will attempt to retrieve "
        "credentials from the instance metadata service."
    )
    def __init__(self, msg):
        final_msg = msg + '\n' + self.MSG
        super(InvalidInstanceMetadataError, self).__init__(final_msg)
