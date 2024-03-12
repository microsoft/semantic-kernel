"""
Exceptions that are specific to the cloudtrail module.
"""
from boto.exception import BotoServerError


class InvalidSnsTopicNameException(BotoServerError):
    """
    Raised when an invalid SNS topic name is passed to Cloudtrail.
    """
    pass


class InvalidS3BucketNameException(BotoServerError):
    """
    Raised when an invalid S3 bucket name is passed to Cloudtrail.
    """
    pass


class TrailAlreadyExistsException(BotoServerError):
    """
    Raised when the given trail name already exists.
    """
    pass


class InsufficientSnsTopicPolicyException(BotoServerError):
    """
    Raised when the SNS topic does not allow Cloudtrail to post
    messages.
    """
    pass


class InvalidTrailNameException(BotoServerError):
    """
    Raised when the trail name is invalid.
    """
    pass


class InternalErrorException(BotoServerError):
    """
    Raised when there was an internal Cloudtrail error.
    """
    pass


class TrailNotFoundException(BotoServerError):
    """
    Raised when the given trail name is not found.
    """
    pass


class S3BucketDoesNotExistException(BotoServerError):
    """
    Raised when the given S3 bucket does not exist.
    """
    pass


class TrailNotProvidedException(BotoServerError):
    """
    Raised when no trail name was provided.
    """
    pass


class InvalidS3PrefixException(BotoServerError):
    """
    Raised when an invalid key prefix is given.
    """
    pass


class MaximumNumberOfTrailsExceededException(BotoServerError):
    """
    Raised when no more trails can be created.
    """
    pass


class InsufficientS3BucketPolicyException(BotoServerError):
    """
    Raised when the S3 bucket does not allow Cloudtrail to
    write files into the prefix.
    """
    pass


class InvalidMaxResultsException(BotoServerError):
    pass


class InvalidTimeRangeException(BotoServerError):
    pass


class InvalidLookupAttributesException(BotoServerError):
    pass


class InvalidCloudWatchLogsLogGroupArnException(BotoServerError):
    pass


class InvalidCloudWatchLogsRoleArnException(BotoServerError):
    pass


class CloudWatchLogsDeliveryUnavailableException(BotoServerError):
    pass


class InvalidNextTokenException(BotoServerError):
    pass
