"""
Exceptions that are specific to the dynamodb module.
"""
from boto.exception import BotoServerError, BotoClientError
from boto.exception import DynamoDBResponseError


class DynamoDBExpiredTokenError(BotoServerError):
    """
    Raised when a DynamoDB security token expires. This is generally boto's
    (or the user's) notice to renew their DynamoDB security tokens.
    """
    pass


class DynamoDBKeyNotFoundError(BotoClientError):
    """
    Raised when attempting to retrieve or interact with an item whose key
    can't be found.
    """
    pass


class DynamoDBItemError(BotoClientError):
    """
    Raised when invalid parameters are passed when creating a
    new Item in DynamoDB.
    """
    pass


class DynamoDBNumberError(BotoClientError):
    """
    Raised in the event of incompatible numeric type casting.
    """
    pass


class DynamoDBConditionalCheckFailedError(DynamoDBResponseError):
    """
    Raised when a ConditionalCheckFailedException response is received.
    This happens when a conditional check, expressed via the expected_value
    paramenter, fails.
    """
    pass


class DynamoDBValidationError(DynamoDBResponseError):
    """
    Raised when a ValidationException response is received. This happens
    when one or more required parameter values are missing, or if the item
    has exceeded the 64Kb size limit.
    """
    pass


class DynamoDBThroughputExceededError(DynamoDBResponseError):
    """
    Raised when the provisioned throughput has been exceeded.
    Normally, when provisioned throughput is exceeded the operation
    is retried.  If the retries are exhausted then this exception
    will be raised.
    """
    pass
