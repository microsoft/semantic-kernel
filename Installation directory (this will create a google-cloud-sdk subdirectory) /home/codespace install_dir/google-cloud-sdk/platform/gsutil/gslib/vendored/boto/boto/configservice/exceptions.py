# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from boto.exception import BotoServerError


class InvalidLimitException(BotoServerError):
    pass


class NoSuchBucketException(BotoServerError):
    pass


class InvalidSNSTopicARNException(BotoServerError):
    pass


class ResourceNotDiscoveredException(BotoServerError):
    pass


class MaxNumberOfDeliveryChannelsExceededException(BotoServerError):
    pass


class LastDeliveryChannelDeleteFailedException(BotoServerError):
    pass


class InsufficientDeliveryPolicyException(BotoServerError):
    pass


class InvalidRoleException(BotoServerError):
    pass


class InvalidTimeRangeException(BotoServerError):
    pass


class NoSuchDeliveryChannelException(BotoServerError):
    pass


class NoSuchConfigurationRecorderException(BotoServerError):
    pass


class InvalidS3KeyPrefixException(BotoServerError):
    pass


class InvalidDeliveryChannelNameException(BotoServerError):
    pass


class NoRunningConfigurationRecorderException(BotoServerError):
    pass


class ValidationException(BotoServerError):
    pass


class NoAvailableConfigurationRecorderException(BotoServerError):
    pass


class InvalidNextTokenException(BotoServerError):
    pass


class InvalidConfigurationRecorderNameException(BotoServerError):
    pass


class NoAvailableDeliveryChannelException(BotoServerError):
    pass


class MaxNumberOfConfigurationRecordersExceededException(BotoServerError):
    pass
