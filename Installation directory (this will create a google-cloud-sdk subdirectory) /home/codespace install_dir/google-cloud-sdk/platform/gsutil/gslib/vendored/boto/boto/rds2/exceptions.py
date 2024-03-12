# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.exception import JSONResponseError


class InvalidSubnet(JSONResponseError):
    pass


class DBParameterGroupQuotaExceeded(JSONResponseError):
    pass


class DBSubnetGroupAlreadyExists(JSONResponseError):
    pass


class DBSubnetGroupQuotaExceeded(JSONResponseError):
    pass


class InstanceQuotaExceeded(JSONResponseError):
    pass


class InvalidRestore(JSONResponseError):
    pass


class InvalidDBParameterGroupState(JSONResponseError):
    pass


class AuthorizationQuotaExceeded(JSONResponseError):
    pass


class DBSecurityGroupAlreadyExists(JSONResponseError):
    pass


class InsufficientDBInstanceCapacity(JSONResponseError):
    pass


class ReservedDBInstanceQuotaExceeded(JSONResponseError):
    pass


class DBSecurityGroupNotFound(JSONResponseError):
    pass


class DBInstanceAlreadyExists(JSONResponseError):
    pass


class ReservedDBInstanceNotFound(JSONResponseError):
    pass


class DBSubnetGroupDoesNotCoverEnoughAZs(JSONResponseError):
    pass


class InvalidDBSecurityGroupState(JSONResponseError):
    pass


class InvalidVPCNetworkState(JSONResponseError):
    pass


class ReservedDBInstancesOfferingNotFound(JSONResponseError):
    pass


class SNSTopicArnNotFound(JSONResponseError):
    pass


class SNSNoAuthorization(JSONResponseError):
    pass


class SnapshotQuotaExceeded(JSONResponseError):
    pass


class OptionGroupQuotaExceeded(JSONResponseError):
    pass


class DBParameterGroupNotFound(JSONResponseError):
    pass


class SNSInvalidTopic(JSONResponseError):
    pass


class InvalidDBSubnetGroupState(JSONResponseError):
    pass


class DBSubnetGroupNotFound(JSONResponseError):
    pass


class InvalidOptionGroupState(JSONResponseError):
    pass


class SourceNotFound(JSONResponseError):
    pass


class SubscriptionCategoryNotFound(JSONResponseError):
    pass


class EventSubscriptionQuotaExceeded(JSONResponseError):
    pass


class DBSecurityGroupNotSupported(JSONResponseError):
    pass


class InvalidEventSubscriptionState(JSONResponseError):
    pass


class InvalidDBSubnetState(JSONResponseError):
    pass


class InvalidDBSnapshotState(JSONResponseError):
    pass


class SubscriptionAlreadyExist(JSONResponseError):
    pass


class DBSecurityGroupQuotaExceeded(JSONResponseError):
    pass


class ProvisionedIopsNotAvailableInAZ(JSONResponseError):
    pass


class AuthorizationNotFound(JSONResponseError):
    pass


class OptionGroupAlreadyExists(JSONResponseError):
    pass


class SubscriptionNotFound(JSONResponseError):
    pass


class DBUpgradeDependencyFailure(JSONResponseError):
    pass


class PointInTimeRestoreNotEnabled(JSONResponseError):
    pass


class AuthorizationAlreadyExists(JSONResponseError):
    pass


class DBSubnetQuotaExceeded(JSONResponseError):
    pass


class OptionGroupNotFound(JSONResponseError):
    pass


class DBParameterGroupAlreadyExists(JSONResponseError):
    pass


class DBInstanceNotFound(JSONResponseError):
    pass


class ReservedDBInstanceAlreadyExists(JSONResponseError):
    pass


class InvalidDBInstanceState(JSONResponseError):
    pass


class DBSnapshotNotFound(JSONResponseError):
    pass


class DBSnapshotAlreadyExists(JSONResponseError):
    pass


class StorageQuotaExceeded(JSONResponseError):
    pass


class SubnetAlreadyInUse(JSONResponseError):
    pass
