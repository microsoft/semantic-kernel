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


class InvalidDeploymentIdException(BotoServerError):
    pass


class InvalidDeploymentGroupNameException(BotoServerError):
    pass


class DeploymentConfigAlreadyExistsException(BotoServerError):
    pass


class InvalidRoleException(BotoServerError):
    pass


class RoleRequiredException(BotoServerError):
    pass


class DeploymentGroupAlreadyExistsException(BotoServerError):
    pass


class DeploymentConfigLimitExceededException(BotoServerError):
    pass


class InvalidNextTokenException(BotoServerError):
    pass


class InvalidDeploymentConfigNameException(BotoServerError):
    pass


class InvalidSortByException(BotoServerError):
    pass


class InstanceDoesNotExistException(BotoServerError):
    pass


class InvalidMinimumHealthyHostValueException(BotoServerError):
    pass


class ApplicationLimitExceededException(BotoServerError):
    pass


class ApplicationNameRequiredException(BotoServerError):
    pass


class InvalidEC2TagException(BotoServerError):
    pass


class DeploymentDoesNotExistException(BotoServerError):
    pass


class DeploymentLimitExceededException(BotoServerError):
    pass


class InvalidInstanceStatusException(BotoServerError):
    pass


class RevisionRequiredException(BotoServerError):
    pass


class InvalidBucketNameFilterException(BotoServerError):
    pass


class DeploymentGroupLimitExceededException(BotoServerError):
    pass


class DeploymentGroupDoesNotExistException(BotoServerError):
    pass


class DeploymentConfigNameRequiredException(BotoServerError):
    pass


class DeploymentAlreadyCompletedException(BotoServerError):
    pass


class RevisionDoesNotExistException(BotoServerError):
    pass


class DeploymentGroupNameRequiredException(BotoServerError):
    pass


class DeploymentIdRequiredException(BotoServerError):
    pass


class DeploymentConfigDoesNotExistException(BotoServerError):
    pass


class BucketNameFilterRequiredException(BotoServerError):
    pass


class InvalidTimeRangeException(BotoServerError):
    pass


class ApplicationDoesNotExistException(BotoServerError):
    pass


class InvalidRevisionException(BotoServerError):
    pass


class InvalidSortOrderException(BotoServerError):
    pass


class InvalidOperationException(BotoServerError):
    pass


class InvalidAutoScalingGroupException(BotoServerError):
    pass


class InvalidApplicationNameException(BotoServerError):
    pass


class DescriptionTooLongException(BotoServerError):
    pass


class ApplicationAlreadyExistsException(BotoServerError):
    pass


class InvalidDeployedStateFilterException(BotoServerError):
    pass


class DeploymentNotStartedException(BotoServerError):
    pass


class DeploymentConfigInUseException(BotoServerError):
    pass


class InstanceIdRequiredException(BotoServerError):
    pass


class InvalidKeyPrefixFilterException(BotoServerError):
    pass


class InvalidDeploymentStatusException(BotoServerError):
    pass
