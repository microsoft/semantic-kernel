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

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.cloudhsm import exceptions


class CloudHSMConnection(AWSQueryConnection):
    """
    AWS CloudHSM Service
    """
    APIVersion = "2014-05-30"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cloudhsm.us-east-1.amazonaws.com"
    ServiceName = "CloudHSM"
    TargetPrefix = "CloudHsmFrontendService"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidRequestException": exceptions.InvalidRequestException,
        "CloudHsmServiceException": exceptions.CloudHsmServiceException,
        "CloudHsmInternalException": exceptions.CloudHsmInternalException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(CloudHSMConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_hapg(self, label):
        """
        Creates a high-availability partition group. A high-
        availability partition group is a group of partitions that
        spans multiple physical HSMs.

        :type label: string
        :param label: The label of the new high-availability partition group.

        """
        params = {'Label': label, }
        return self.make_request(action='CreateHapg',
                                 body=json.dumps(params))

    def create_hsm(self, subnet_id, ssh_key, iam_role_arn, subscription_type,
                   eni_ip=None, external_id=None, client_token=None,
                   syslog_ip=None):
        """
        Creates an uninitialized HSM instance. Running this command
        provisions an HSM appliance and will result in charges to your
        AWS account for the HSM.

        :type subnet_id: string
        :param subnet_id: The identifier of the subnet in your VPC in which to
            place the HSM.

        :type ssh_key: string
        :param ssh_key: The SSH public key to install on the HSM.

        :type eni_ip: string
        :param eni_ip: The IP address to assign to the HSM's ENI.

        :type iam_role_arn: string
        :param iam_role_arn: The ARN of an IAM role to enable the AWS CloudHSM
            service to allocate an ENI on your behalf.

        :type external_id: string
        :param external_id: The external ID from **IamRoleArn**, if present.

        :type subscription_type: string
        :param subscription_type: The subscription type.

        :type client_token: string
        :param client_token: A user-defined token to ensure idempotence.
            Subsequent calls to this action with the same token will be
            ignored.

        :type syslog_ip: string
        :param syslog_ip: The IP address for the syslog monitoring server.

        """
        params = {
            'SubnetId': subnet_id,
            'SshKey': ssh_key,
            'IamRoleArn': iam_role_arn,
            'SubscriptionType': subscription_type,
        }
        if eni_ip is not None:
            params['EniIp'] = eni_ip
        if external_id is not None:
            params['ExternalId'] = external_id
        if client_token is not None:
            params['ClientToken'] = client_token
        if syslog_ip is not None:
            params['SyslogIp'] = syslog_ip
        return self.make_request(action='CreateHsm',
                                 body=json.dumps(params))

    def create_luna_client(self, certificate, label=None):
        """
        Creates an HSM client.

        :type label: string
        :param label: The label for the client.

        :type certificate: string
        :param certificate: The contents of a Base64-Encoded X.509 v3
            certificate to be installed on the HSMs used by this client.

        """
        params = {'Certificate': certificate, }
        if label is not None:
            params['Label'] = label
        return self.make_request(action='CreateLunaClient',
                                 body=json.dumps(params))

    def delete_hapg(self, hapg_arn):
        """
        Deletes a high-availability partition group.

        :type hapg_arn: string
        :param hapg_arn: The ARN of the high-availability partition group to
            delete.

        """
        params = {'HapgArn': hapg_arn, }
        return self.make_request(action='DeleteHapg',
                                 body=json.dumps(params))

    def delete_hsm(self, hsm_arn):
        """
        Deletes an HSM. Once complete, this operation cannot be undone
        and your key material cannot be recovered.

        :type hsm_arn: string
        :param hsm_arn: The ARN of the HSM to delete.

        """
        params = {'HsmArn': hsm_arn, }
        return self.make_request(action='DeleteHsm',
                                 body=json.dumps(params))

    def delete_luna_client(self, client_arn):
        """
        Deletes a client.

        :type client_arn: string
        :param client_arn: The ARN of the client to delete.

        """
        params = {'ClientArn': client_arn, }
        return self.make_request(action='DeleteLunaClient',
                                 body=json.dumps(params))

    def describe_hapg(self, hapg_arn):
        """
        Retrieves information about a high-availability partition
        group.

        :type hapg_arn: string
        :param hapg_arn: The ARN of the high-availability partition group to
            describe.

        """
        params = {'HapgArn': hapg_arn, }
        return self.make_request(action='DescribeHapg',
                                 body=json.dumps(params))

    def describe_hsm(self, hsm_arn=None, hsm_serial_number=None):
        """
        Retrieves information about an HSM. You can identify the HSM
        by its ARN or its serial number.

        :type hsm_arn: string
        :param hsm_arn: The ARN of the HSM. Either the HsmArn or the
            SerialNumber parameter must be specified.

        :type hsm_serial_number: string
        :param hsm_serial_number: The serial number of the HSM. Either the
            HsmArn or the HsmSerialNumber parameter must be specified.

        """
        params = {}
        if hsm_arn is not None:
            params['HsmArn'] = hsm_arn
        if hsm_serial_number is not None:
            params['HsmSerialNumber'] = hsm_serial_number
        return self.make_request(action='DescribeHsm',
                                 body=json.dumps(params))

    def describe_luna_client(self, client_arn=None,
                             certificate_fingerprint=None):
        """
        Retrieves information about an HSM client.

        :type client_arn: string
        :param client_arn: The ARN of the client.

        :type certificate_fingerprint: string
        :param certificate_fingerprint: The certificate fingerprint.

        """
        params = {}
        if client_arn is not None:
            params['ClientArn'] = client_arn
        if certificate_fingerprint is not None:
            params['CertificateFingerprint'] = certificate_fingerprint
        return self.make_request(action='DescribeLunaClient',
                                 body=json.dumps(params))

    def get_config(self, client_arn, client_version, hapg_list):
        """
        Gets the configuration files necessary to connect to all high
        availability partition groups the client is associated with.

        :type client_arn: string
        :param client_arn: The ARN of the client.

        :type client_version: string
        :param client_version: The client version.

        :type hapg_list: list
        :param hapg_list: A list of ARNs that identify the high-availability
            partition groups that are associated with the client.

        """
        params = {
            'ClientArn': client_arn,
            'ClientVersion': client_version,
            'HapgList': hapg_list,
        }
        return self.make_request(action='GetConfig',
                                 body=json.dumps(params))

    def list_available_zones(self):
        """
        Lists the Availability Zones that have available AWS CloudHSM
        capacity.

        
        """
        params = {}
        return self.make_request(action='ListAvailableZones',
                                 body=json.dumps(params))

    def list_hapgs(self, next_token=None):
        """
        Lists the high-availability partition groups for the account.

        This operation supports pagination with the use of the
        NextToken member. If more results are available, the NextToken
        member of the response contains a token that you pass in the
        next call to ListHapgs to retrieve the next set of items.

        :type next_token: string
        :param next_token: The NextToken value from a previous call to
            ListHapgs. Pass null if this is the first call.

        """
        params = {}
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='ListHapgs',
                                 body=json.dumps(params))

    def list_hsms(self, next_token=None):
        """
        Retrieves the identifiers of all of the HSMs provisioned for
        the current customer.

        This operation supports pagination with the use of the
        NextToken member. If more results are available, the NextToken
        member of the response contains a token that you pass in the
        next call to ListHsms to retrieve the next set of items.

        :type next_token: string
        :param next_token: The NextToken value from a previous call to
            ListHsms. Pass null if this is the first call.

        """
        params = {}
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='ListHsms',
                                 body=json.dumps(params))

    def list_luna_clients(self, next_token=None):
        """
        Lists all of the clients.

        This operation supports pagination with the use of the
        NextToken member. If more results are available, the NextToken
        member of the response contains a token that you pass in the
        next call to ListLunaClients to retrieve the next set of
        items.

        :type next_token: string
        :param next_token: The NextToken value from a previous call to
            ListLunaClients. Pass null if this is the first call.

        """
        params = {}
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='ListLunaClients',
                                 body=json.dumps(params))

    def modify_hapg(self, hapg_arn, label=None, partition_serial_list=None):
        """
        Modifies an existing high-availability partition group.

        :type hapg_arn: string
        :param hapg_arn: The ARN of the high-availability partition group to
            modify.

        :type label: string
        :param label: The new label for the high-availability partition group.

        :type partition_serial_list: list
        :param partition_serial_list: The list of partition serial numbers to
            make members of the high-availability partition group.

        """
        params = {'HapgArn': hapg_arn, }
        if label is not None:
            params['Label'] = label
        if partition_serial_list is not None:
            params['PartitionSerialList'] = partition_serial_list
        return self.make_request(action='ModifyHapg',
                                 body=json.dumps(params))

    def modify_hsm(self, hsm_arn, subnet_id=None, eni_ip=None,
                   iam_role_arn=None, external_id=None, syslog_ip=None):
        """
        Modifies an HSM.

        :type hsm_arn: string
        :param hsm_arn: The ARN of the HSM to modify.

        :type subnet_id: string
        :param subnet_id: The new identifier of the subnet that the HSM is in.

        :type eni_ip: string
        :param eni_ip: The new IP address for the elastic network interface
            attached to the HSM.

        :type iam_role_arn: string
        :param iam_role_arn: The new IAM role ARN.

        :type external_id: string
        :param external_id: The new external ID.

        :type syslog_ip: string
        :param syslog_ip: The new IP address for the syslog monitoring server.

        """
        params = {'HsmArn': hsm_arn, }
        if subnet_id is not None:
            params['SubnetId'] = subnet_id
        if eni_ip is not None:
            params['EniIp'] = eni_ip
        if iam_role_arn is not None:
            params['IamRoleArn'] = iam_role_arn
        if external_id is not None:
            params['ExternalId'] = external_id
        if syslog_ip is not None:
            params['SyslogIp'] = syslog_ip
        return self.make_request(action='ModifyHsm',
                                 body=json.dumps(params))

    def modify_luna_client(self, client_arn, certificate):
        """
        Modifies the certificate used by the client.

        This action can potentially start a workflow to install the
        new certificate on the client's HSMs.

        :type client_arn: string
        :param client_arn: The ARN of the client.

        :type certificate: string
        :param certificate: The new certificate for the client.

        """
        params = {
            'ClientArn': client_arn,
            'Certificate': certificate,
        }
        return self.make_request(action='ModifyLunaClient',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

