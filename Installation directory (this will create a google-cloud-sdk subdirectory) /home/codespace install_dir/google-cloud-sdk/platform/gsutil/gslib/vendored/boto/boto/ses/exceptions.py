"""
Various exceptions that are specific to the SES module.
"""
from boto.exception import BotoServerError


class SESError(BotoServerError):
    """
    Sub-class all SES-related errors from here. Don't raise this error
    directly from anywhere. The only thing this gets us is the ability to
    catch SESErrors separately from the more generic, top-level
    BotoServerError exception.
    """
    pass


class SESAddressNotVerifiedError(SESError):
    """
    Raised when a "Reply-To" address has not been validated in SES yet.
    """
    pass


class SESIdentityNotVerifiedError(SESError):
    """
    Raised when an identity (domain or address) has not been verified in SES yet.
    """
    pass


class SESDomainNotConfirmedError(SESError):
    """
    """
    pass


class SESAddressBlacklistedError(SESError):
    """
    After you attempt to send mail to an address, and delivery repeatedly
    fails, said address is blacklisted for at least 24 hours. The blacklisting
    eventually expires, and you are able to attempt delivery again. If you
    attempt to send mail to a blacklisted email, this is raised.
    """
    pass


class SESDailyQuotaExceededError(SESError):
    """
    Your account's daily (rolling 24 hour total) allotment of outbound emails
    has been exceeded.
    """
    pass


class SESMaxSendingRateExceededError(SESError):
    """
    Your account's requests/second limit has been exceeded.
    """
    pass


class SESDomainEndsWithDotError(SESError):
    """
    Recipient's email address' domain ends with a period/dot.
    """
    pass


class SESLocalAddressCharacterError(SESError):
    """
    An address contained a control or whitespace character.
    """
    pass


class SESIllegalAddressError(SESError):
    """
    Raised when an illegal address is encountered.
    """
    pass
