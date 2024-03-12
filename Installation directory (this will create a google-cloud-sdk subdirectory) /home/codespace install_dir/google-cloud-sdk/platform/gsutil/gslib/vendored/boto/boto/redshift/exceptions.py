# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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


class ClusterNotFoundFault(JSONResponseError):
    pass


class InvalidClusterSnapshotStateFault(JSONResponseError):
    pass


class ClusterSnapshotNotFoundFault(JSONResponseError):
    pass


class ClusterSecurityGroupQuotaExceededFault(JSONResponseError):
    pass


class ReservedNodeOfferingNotFoundFault(JSONResponseError):
    pass


class InvalidSubnet(JSONResponseError):
    pass


class ClusterSubnetGroupQuotaExceededFault(JSONResponseError):
    pass


class InvalidClusterStateFault(JSONResponseError):
    pass


class InvalidClusterParameterGroupStateFault(JSONResponseError):
    pass


class ClusterParameterGroupAlreadyExistsFault(JSONResponseError):
    pass


class InvalidClusterSecurityGroupStateFault(JSONResponseError):
    pass


class InvalidRestoreFault(JSONResponseError):
    pass


class AuthorizationNotFoundFault(JSONResponseError):
    pass


class ResizeNotFoundFault(JSONResponseError):
    pass


class NumberOfNodesQuotaExceededFault(JSONResponseError):
    pass


class ClusterSnapshotAlreadyExistsFault(JSONResponseError):
    pass


class AuthorizationQuotaExceededFault(JSONResponseError):
    pass


class AuthorizationAlreadyExistsFault(JSONResponseError):
    pass


class ClusterSnapshotQuotaExceededFault(JSONResponseError):
    pass


class ReservedNodeNotFoundFault(JSONResponseError):
    pass


class ReservedNodeAlreadyExistsFault(JSONResponseError):
    pass


class ClusterSecurityGroupAlreadyExistsFault(JSONResponseError):
    pass


class ClusterParameterGroupNotFoundFault(JSONResponseError):
    pass


class ReservedNodeQuotaExceededFault(JSONResponseError):
    pass


class ClusterQuotaExceededFault(JSONResponseError):
    pass


class ClusterSubnetQuotaExceededFault(JSONResponseError):
    pass


class UnsupportedOptionFault(JSONResponseError):
    pass


class InvalidVPCNetworkStateFault(JSONResponseError):
    pass


class ClusterSecurityGroupNotFoundFault(JSONResponseError):
    pass


class InvalidClusterSubnetGroupStateFault(JSONResponseError):
    pass


class ClusterSubnetGroupAlreadyExistsFault(JSONResponseError):
    pass


class NumberOfNodesPerClusterLimitExceededFault(JSONResponseError):
    pass


class ClusterSubnetGroupNotFoundFault(JSONResponseError):
    pass


class ClusterParameterGroupQuotaExceededFault(JSONResponseError):
    pass


class ClusterAlreadyExistsFault(JSONResponseError):
    pass


class InsufficientClusterCapacityFault(JSONResponseError):
    pass


class InvalidClusterSubnetStateFault(JSONResponseError):
    pass


class SubnetAlreadyInUse(JSONResponseError):
    pass


class InvalidParameterCombinationFault(JSONResponseError):
    pass


class AccessToSnapshotDeniedFault(JSONResponseError):
    pass


class UnauthorizedOperationFault(JSONResponseError):
    pass


class SnapshotCopyAlreadyDisabled(JSONResponseError):
    pass


class ClusterNotFound(JSONResponseError):
    pass


class UnknownSnapshotCopyRegion(JSONResponseError):
    pass


class InvalidClusterSubnetState(JSONResponseError):
    pass


class ReservedNodeQuotaExceeded(JSONResponseError):
    pass


class InvalidClusterState(JSONResponseError):
    pass


class HsmClientCertificateQuotaExceeded(JSONResponseError):
    pass


class SubscriptionCategoryNotFound(JSONResponseError):
    pass


class HsmClientCertificateNotFound(JSONResponseError):
    pass


class SubscriptionEventIdNotFound(JSONResponseError):
    pass


class ClusterSecurityGroupAlreadyExists(JSONResponseError):
    pass


class HsmConfigurationAlreadyExists(JSONResponseError):
    pass


class NumberOfNodesQuotaExceeded(JSONResponseError):
    pass


class ReservedNodeOfferingNotFound(JSONResponseError):
    pass


class BucketNotFound(JSONResponseError):
    pass


class InsufficientClusterCapacity(JSONResponseError):
    pass


class InvalidRestore(JSONResponseError):
    pass


class UnauthorizedOperation(JSONResponseError):
    pass


class ClusterQuotaExceeded(JSONResponseError):
    pass


class InvalidVPCNetworkState(JSONResponseError):
    pass


class ClusterSnapshotNotFound(JSONResponseError):
    pass


class AuthorizationQuotaExceeded(JSONResponseError):
    pass


class InvalidHsmClientCertificateState(JSONResponseError):
    pass


class SNSTopicArnNotFound(JSONResponseError):
    pass


class ResizeNotFound(JSONResponseError):
    pass


class ClusterSubnetGroupNotFound(JSONResponseError):
    pass


class SNSNoAuthorization(JSONResponseError):
    pass


class ClusterSnapshotQuotaExceeded(JSONResponseError):
    pass


class AccessToSnapshotDenied(JSONResponseError):
    pass


class InvalidClusterSecurityGroupState(JSONResponseError):
    pass


class NumberOfNodesPerClusterLimitExceeded(JSONResponseError):
    pass


class ClusterSubnetQuotaExceeded(JSONResponseError):
    pass


class SNSInvalidTopic(JSONResponseError):
    pass


class ClusterSecurityGroupNotFound(JSONResponseError):
    pass


class InvalidElasticIp(JSONResponseError):
    pass


class InvalidClusterParameterGroupState(JSONResponseError):
    pass


class InvalidHsmConfigurationState(JSONResponseError):
    pass



class ClusterAlreadyExists(JSONResponseError):
    pass


class HsmConfigurationQuotaExceeded(JSONResponseError):
    pass


class ClusterSnapshotAlreadyExists(JSONResponseError):
    pass


class SubscriptionSeverityNotFound(JSONResponseError):
    pass


class SourceNotFound(JSONResponseError):
    pass


class ReservedNodeAlreadyExists(JSONResponseError):
    pass


class ClusterSubnetGroupQuotaExceeded(JSONResponseError):
    pass


class ClusterParameterGroupNotFound(JSONResponseError):
    pass


class InvalidS3BucketName(JSONResponseError):
    pass


class InvalidS3KeyPrefix(JSONResponseError):
    pass


class SubscriptionAlreadyExist(JSONResponseError):
    pass


class HsmConfigurationNotFound(JSONResponseError):
    pass


class AuthorizationNotFound(JSONResponseError):
    pass


class ClusterSecurityGroupQuotaExceeded(JSONResponseError):
    pass


class EventSubscriptionQuotaExceeded(JSONResponseError):
    pass


class AuthorizationAlreadyExists(JSONResponseError):
    pass


class InvalidClusterSnapshotState(JSONResponseError):
    pass


class ClusterParameterGroupQuotaExceeded(JSONResponseError):
    pass


class SnapshotCopyDisabled(JSONResponseError):
    pass


class ClusterSubnetGroupAlreadyExists(JSONResponseError):
    pass


class ReservedNodeNotFound(JSONResponseError):
    pass


class HsmClientCertificateAlreadyExists(JSONResponseError):
    pass


class InvalidClusterSubnetGroupState(JSONResponseError):
    pass


class SubscriptionNotFound(JSONResponseError):
    pass


class InsufficientS3BucketPolicy(JSONResponseError):
    pass


class ClusterParameterGroupAlreadyExists(JSONResponseError):
    pass


class UnsupportedOption(JSONResponseError):
    pass


class CopyToRegionDisabled(JSONResponseError):
    pass


class SnapshotCopyAlreadyEnabled(JSONResponseError):
    pass


class IncompatibleOrderableOptions(JSONResponseError):
    pass


class InvalidSubscriptionState(JSONResponseError):
    pass
