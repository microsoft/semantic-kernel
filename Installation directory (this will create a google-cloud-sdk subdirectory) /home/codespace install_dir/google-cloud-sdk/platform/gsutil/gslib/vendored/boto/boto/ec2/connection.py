# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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

"""
Represents a connection to the EC2 service.
"""

import base64
import warnings
from datetime import datetime
from datetime import timedelta

import boto
from boto.auth import detect_potential_sigv4
from boto.connection import AWSQueryConnection
from boto.resultset import ResultSet
from boto.ec2.image import Image, ImageAttribute, CopyImage
from boto.ec2.instance import Reservation, Instance
from boto.ec2.instance import ConsoleOutput, InstanceAttribute
from boto.ec2.keypair import KeyPair
from boto.ec2.address import Address
from boto.ec2.volume import Volume, VolumeAttribute
from boto.ec2.snapshot import Snapshot
from boto.ec2.snapshot import SnapshotAttribute
from boto.ec2.zone import Zone
from boto.ec2.securitygroup import SecurityGroup
from boto.ec2.regioninfo import RegionInfo
from boto.ec2.instanceinfo import InstanceInfo
from boto.ec2.reservedinstance import ReservedInstancesOffering
from boto.ec2.reservedinstance import ReservedInstance
from boto.ec2.reservedinstance import ReservedInstanceListing
from boto.ec2.reservedinstance import ReservedInstancesConfiguration
from boto.ec2.reservedinstance import ModifyReservedInstancesResult
from boto.ec2.reservedinstance import ReservedInstancesModification
from boto.ec2.spotinstancerequest import SpotInstanceRequest
from boto.ec2.spotpricehistory import SpotPriceHistory
from boto.ec2.spotdatafeedsubscription import SpotDatafeedSubscription
from boto.ec2.bundleinstance import BundleInstanceTask
from boto.ec2.placementgroup import PlacementGroup
from boto.ec2.tag import Tag
from boto.ec2.instancetype import InstanceType
from boto.ec2.instancestatus import InstanceStatusSet
from boto.ec2.volumestatus import VolumeStatusSet
from boto.ec2.networkinterface import NetworkInterface
from boto.ec2.attributes import AccountAttribute, VPCAttribute
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
from boto.exception import EC2ResponseError
from boto.compat import six

#boto.set_stream_logger('ec2')


class EC2Connection(AWSQueryConnection):

    APIVersion = boto.config.get('Boto', 'ec2_version', '2014-10-01')
    DefaultRegionName = boto.config.get('Boto', 'ec2_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto', 'ec2_region_endpoint',
                                            'ec2.us-east-1.amazonaws.com')
    ResponseError = EC2ResponseError

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, host=None, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 api_version=None, security_token=None,
                 validate_certs=True, profile_name=None):
        """
        Init method to create a new connection to EC2.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region
        super(EC2Connection, self).__init__(aws_access_key_id,
                                            aws_secret_access_key,
                                            is_secure, port, proxy, proxy_port,
                                            proxy_user, proxy_pass,
                                            self.region.endpoint, debug,
                                            https_connection_factory, path,
                                            security_token,
                                            validate_certs=validate_certs,
                                            profile_name=profile_name)
        if api_version:
            self.APIVersion = api_version

    def _required_auth_capability(self):
        return ['hmac-v4']

    def get_params(self):
        """
        Returns a dictionary containing the value of all of the keyword
        arguments passed when constructing this connection.
        """
        param_names = ['aws_access_key_id', 'aws_secret_access_key',
                       'is_secure', 'port', 'proxy', 'proxy_port',
                       'proxy_user', 'proxy_pass',
                       'debug', 'https_connection_factory']
        params = {}
        for name in param_names:
            params[name] = getattr(self, name)
        return params

    def build_filter_params(self, params, filters):
        if not isinstance(filters, dict):
            filters = dict(filters)

        i = 1
        for name in filters:
            aws_name = name
            if not aws_name.startswith('tag:'):
                aws_name = name.replace('_', '-')
            params['Filter.%d.Name' % i] = aws_name
            value = filters[name]
            if not isinstance(value, list):
                value = [value]
            j = 1
            for v in value:
                params['Filter.%d.Value.%d' % (i, j)] = v
                j += 1
            i += 1

    # Image methods

    def get_all_images(self, image_ids=None, owners=None,
                       executable_by=None, filters=None, dry_run=False):
        """
        Retrieve all the EC2 images available on your account.

        :type image_ids: list
        :param image_ids: A list of strings with the image IDs wanted

        :type owners: list
        :param owners: A list of owner IDs, the special strings 'self',
            'amazon', and 'aws-marketplace', may be used to describe
            images owned by you, Amazon or AWS Marketplace
            respectively

        :type executable_by: list
        :param executable_by: Returns AMIs for which the specified
                              user ID has explicit launch permissions

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.image.Image`
        """
        params = {}
        if image_ids:
            self.build_list_params(params, image_ids, 'ImageId')
        if owners:
            self.build_list_params(params, owners, 'Owner')
        if executable_by:
            self.build_list_params(params, executable_by, 'ExecutableBy')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeImages', params,
                             [('item', Image)], verb='POST')

    def get_all_kernels(self, kernel_ids=None, owners=None, dry_run=False):
        """
        Retrieve all the EC2 kernels available on your account.
        Constructs a filter to allow the processing to happen server side.

        :type kernel_ids: list
        :param kernel_ids: A list of strings with the image IDs wanted

        :type owners: list
        :param owners: A list of owner IDs

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.image.Image`
        """
        params = {}
        if kernel_ids:
            self.build_list_params(params, kernel_ids, 'ImageId')
        if owners:
            self.build_list_params(params, owners, 'Owner')
        filter = {'image-type': 'kernel'}
        self.build_filter_params(params, filter)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeImages', params,
                             [('item', Image)], verb='POST')

    def get_all_ramdisks(self, ramdisk_ids=None, owners=None, dry_run=False):
        """
        Retrieve all the EC2 ramdisks available on your account.
        Constructs a filter to allow the processing to happen server side.

        :type ramdisk_ids: list
        :param ramdisk_ids: A list of strings with the image IDs wanted

        :type owners: list
        :param owners: A list of owner IDs

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.image.Image`
        """
        params = {}
        if ramdisk_ids:
            self.build_list_params(params, ramdisk_ids, 'ImageId')
        if owners:
            self.build_list_params(params, owners, 'Owner')
        filter = {'image-type': 'ramdisk'}
        self.build_filter_params(params, filter)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeImages', params,
                             [('item', Image)], verb='POST')

    def get_image(self, image_id, dry_run=False):
        """
        Shortcut method to retrieve a specific image (AMI).

        :type image_id: string
        :param image_id: the ID of the Image to retrieve

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.image.Image`
        :return: The EC2 Image specified or None if the image is not found
        """
        try:
            return self.get_all_images(image_ids=[image_id], dry_run=dry_run)[0]
        except IndexError:  # None of those images available
            return None

    def register_image(self, name=None, description=None, image_location=None,
                       architecture=None, kernel_id=None, ramdisk_id=None,
                       root_device_name=None, block_device_map=None,
                       dry_run=False, virtualization_type=None,
                       sriov_net_support=None,
                       snapshot_id=None,
                       delete_root_volume_on_termination=False):
        """
        Register an image.

        :type name: string
        :param name: The name of the AMI.  Valid only for EBS-based images.

        :type description: string
        :param description: The description of the AMI.

        :type image_location: string
        :param image_location: Full path to your AMI manifest in
            Amazon S3 storage.  Only used for S3-based AMI's.

        :type architecture: string
        :param architecture: The architecture of the AMI.  Valid choices are:
            * i386
            * x86_64

        :type kernel_id: string
        :param kernel_id: The ID of the kernel with which to launch
            the instances

        :type root_device_name: string
        :param root_device_name: The root device name (e.g. /dev/sdh)

        :type block_device_map: :class:`boto.ec2.blockdevicemapping.BlockDeviceMapping`
        :param block_device_map: A BlockDeviceMapping data structure
            describing the EBS volumes associated with the Image.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type virtualization_type: string
        :param virtualization_type: The virutalization_type of the image.
            Valid choices are:
            * paravirtual
            * hvm

        :type sriov_net_support: string
        :param sriov_net_support: Advanced networking support.
            Valid choices are:
            * simple

        :type snapshot_id: string
        :param snapshot_id: A snapshot ID for the snapshot to be used
            as root device for the image. Mutually exclusive with
            block_device_map, requires root_device_name

        :type delete_root_volume_on_termination: bool
        :param delete_root_volume_on_termination: Whether to delete the root
            volume of the image after instance termination. Only applies when
            creating image from snapshot_id. Defaults to False.  Note that
            leaving volumes behind after instance termination is not free.

        :rtype: string
        :return: The new image id
        """
        params = {}
        if name:
            params['Name'] = name
        if description:
            params['Description'] = description
        if architecture:
            params['Architecture'] = architecture
        if kernel_id:
            params['KernelId'] = kernel_id
        if ramdisk_id:
            params['RamdiskId'] = ramdisk_id
        if image_location:
            params['ImageLocation'] = image_location
        if root_device_name:
            params['RootDeviceName'] = root_device_name
        if snapshot_id:
            root_vol = BlockDeviceType(snapshot_id=snapshot_id,
                delete_on_termination=delete_root_volume_on_termination)
            block_device_map = BlockDeviceMapping()
            block_device_map[root_device_name] = root_vol
        if block_device_map:
            block_device_map.ec2_build_list_params(params)
        if dry_run:
            params['DryRun'] = 'true'
        if virtualization_type:
            params['VirtualizationType'] = virtualization_type
        if sriov_net_support:
            params['SriovNetSupport'] = sriov_net_support

        rs = self.get_object('RegisterImage', params, ResultSet, verb='POST')
        image_id = getattr(rs, 'imageId', None)
        return image_id

    def deregister_image(self, image_id, delete_snapshot=False, dry_run=False):
        """
        Unregister an AMI.

        :type image_id: string
        :param image_id: the ID of the Image to unregister

        :type delete_snapshot: bool
        :param delete_snapshot: Set to True if we should delete the
            snapshot associated with an EBS volume mounted at /dev/sda1

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        snapshot_id = None
        if delete_snapshot:
            image = self.get_image(image_id)
            for key in image.block_device_mapping:
                if key == "/dev/sda1":
                    snapshot_id = image.block_device_mapping[key].snapshot_id
                    break
        params = {
            'ImageId': image_id,
        }
        if dry_run:
            params['DryRun'] = 'true'
        result = self.get_status('DeregisterImage',
                                 params, verb='POST')
        if result and snapshot_id:
            return result and self.delete_snapshot(snapshot_id)
        return result

    def create_image(self, instance_id, name,
                     description=None, no_reboot=False,
                     block_device_mapping=None, dry_run=False):
        """
        Will create an AMI from the instance in the running or stopped
        state.

        :type instance_id: string
        :param instance_id: the ID of the instance to image.

        :type name: string
        :param name: The name of the new image

        :type description: string
        :param description: An optional human-readable string describing
            the contents and purpose of the AMI.

        :type no_reboot: bool
        :param no_reboot: An optional flag indicating that the
            bundling process should not attempt to shutdown the
            instance before bundling.  If this flag is True, the
            responsibility of maintaining file system integrity is
            left to the owner of the instance.

        :type block_device_mapping: :class:`boto.ec2.blockdevicemapping.BlockDeviceMapping`
        :param block_device_mapping: A BlockDeviceMapping data structure
            describing the EBS volumes associated with the Image.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: string
        :return: The new image id
        """
        params = {'InstanceId': instance_id,
                  'Name': name}
        if description:
            params['Description'] = description
        if no_reboot:
            params['NoReboot'] = 'true'
        if block_device_mapping:
            block_device_mapping.ec2_build_list_params(params)
        if dry_run:
            params['DryRun'] = 'true'
        img = self.get_object('CreateImage', params, Image, verb='POST')
        return img.id

    # ImageAttribute methods

    def get_image_attribute(self, image_id, attribute='launchPermission',
                            dry_run=False):
        """
        Gets an attribute from an image.

        :type image_id: string
        :param image_id: The Amazon image id for which you want info about

        :type attribute: string
        :param attribute: The attribute you need information about.
            Valid choices are:
            * launchPermission
            * productCodes
            * blockDeviceMapping

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.image.ImageAttribute`
        :return: An ImageAttribute object representing the value of the
                 attribute requested
        """
        params = {'ImageId': image_id,
                  'Attribute': attribute}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeImageAttribute', params,
                               ImageAttribute, verb='POST')

    def modify_image_attribute(self, image_id, attribute='launchPermission',
                               operation='add', user_ids=None, groups=None,
                               product_codes=None, dry_run=False):
        """
        Changes an attribute of an image.

        :type image_id: string
        :param image_id: The image id you wish to change

        :type attribute: string
        :param attribute: The attribute you wish to change

        :type operation: string
        :param operation: Either add or remove (this is required for changing
            launchPermissions)

        :type user_ids: list
        :param user_ids: The Amazon IDs of users to add/remove attributes

        :type groups: list
        :param groups: The groups to add/remove attributes

        :type product_codes: list
        :param product_codes: Amazon DevPay product code. Currently only one
            product code can be associated with an AMI. Once
            set, the product code cannot be changed or reset.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'ImageId': image_id,
                  'Attribute': attribute,
                  'OperationType': operation}
        if user_ids:
            self.build_list_params(params, user_ids, 'UserId')
        if groups:
            self.build_list_params(params, groups, 'UserGroup')
        if product_codes:
            self.build_list_params(params, product_codes, 'ProductCode')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifyImageAttribute', params, verb='POST')

    def reset_image_attribute(self, image_id, attribute='launchPermission',
                              dry_run=False):
        """
        Resets an attribute of an AMI to its default value.

        :type image_id: string
        :param image_id: ID of the AMI for which an attribute will be described

        :type attribute: string
        :param attribute: The attribute to reset

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        params = {'ImageId': image_id,
                  'Attribute': attribute}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ResetImageAttribute', params, verb='POST')

    # Instance methods

    def get_all_instances(self, instance_ids=None, filters=None, dry_run=False,
                          max_results=None):
        """
        Retrieve all the instance reservations associated with your account.

        .. note::
        This method's current behavior is deprecated in favor of
        :meth:`get_all_reservations`.  A future major release will change
        :meth:`get_all_instances` to return a list of
        :class:`boto.ec2.instance.Instance` objects as its name suggests.
        To obtain that behavior today, use :meth:`get_only_instances`.

        :type instance_ids: list
        :param instance_ids: A list of strings of instance IDs

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :rtype: list
        :return: A list of  :class:`boto.ec2.instance.Reservation`

        """
        warnings.warn(('The current get_all_instances implementation will be '
                       'replaced with get_all_reservations.'),
                      PendingDeprecationWarning)
        return self.get_all_reservations(instance_ids=instance_ids,
                                         filters=filters, dry_run=dry_run,
                                         max_results=max_results)

    def get_only_instances(self, instance_ids=None, filters=None,
                           dry_run=False, max_results=None):
        # A future release should rename this method to get_all_instances
        # and make get_only_instances an alias for that.
        """
        Retrieve all the instances associated with your account.

        :type instance_ids: list
        :param instance_ids: A list of strings of instance IDs

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :rtype: list
        :return: A list of  :class:`boto.ec2.instance.Instance`
        """
        next_token = None
        retval = []
        while True:
            reservations = self.get_all_reservations(instance_ids=instance_ids,
                                                     filters=filters,
                                                     dry_run=dry_run,
                                                     max_results=max_results,
                                                     next_token=next_token)
            retval.extend([instance for reservation in reservations for
                           instance in reservation.instances])
            next_token = reservations.next_token
            if not next_token:
                break

        return retval

    def get_all_reservations(self, instance_ids=None, filters=None,
                             dry_run=False, max_results=None, next_token=None):
        """
        Retrieve all the instance reservations associated with your account.

        :type instance_ids: list
        :param instance_ids: A list of strings of instance IDs

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :type next_token: str
        :param next_token: A string specifying the next paginated set
            of results to return.

        :rtype: list
        :return: A list of  :class:`boto.ec2.instance.Reservation`
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if filters:
            if 'group-id' in filters:
                gid = filters.get('group-id')
                if not gid.startswith('sg-') or len(gid) != 11:
                    warnings.warn(
                        "The group-id filter now requires a security group "
                        "identifier (sg-*) instead of a group name. To filter "
                        "by group name use the 'group-name' filter instead.",
                        UserWarning)
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeInstances', params,
                             [('item', Reservation)], verb='POST')

    def get_all_instance_status(self, instance_ids=None,
                                max_results=None, next_token=None,
                                filters=None, dry_run=False,
                                include_all_instances=False):
        """
        Retrieve all the instances in your account scheduled for maintenance.

        :type instance_ids: list
        :param instance_ids: A list of strings of instance IDs

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :type next_token: str
        :param next_token: A string specifying the next paginated set
            of results to return.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
            the results returned.  Filters are provided
            in the form of a dictionary consisting of
            filter names as the key and filter values
            as the value.  The set of allowable filter
            names/values is dependent on the request
            being performed.  Check the EC2 API guide
            for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type include_all_instances: bool
        :param include_all_instances: Set to True if all
            instances should be returned. (Only running
            instances are included by default.)

        :rtype: list
        :return: A list of instances that have maintenance scheduled.
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if max_results:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        if include_all_instances:
            params['IncludeAllInstances'] = 'true'
        return self.get_object('DescribeInstanceStatus', params,
                               InstanceStatusSet, verb='POST')

    def run_instances(self, image_id, min_count=1, max_count=1,
                      key_name=None, security_groups=None,
                      user_data=None, addressing_type=None,
                      instance_type='m1.small', placement=None,
                      kernel_id=None, ramdisk_id=None,
                      monitoring_enabled=False, subnet_id=None,
                      block_device_map=None,
                      disable_api_termination=False,
                      instance_initiated_shutdown_behavior=None,
                      private_ip_address=None,
                      placement_group=None, client_token=None,
                      security_group_ids=None,
                      additional_info=None, instance_profile_name=None,
                      instance_profile_arn=None, tenancy=None,
                      ebs_optimized=False, network_interfaces=None,
                      dry_run=False):
        """
        Runs an image on EC2.

        :type image_id: string
        :param image_id: The ID of the image to run.

        :type min_count: int
        :param min_count: The minimum number of instances to launch.

        :type max_count: int
        :param max_count: The maximum number of instances to launch.

        :type key_name: string
        :param key_name: The name of the key pair with which to
            launch instances.

        :type security_groups: list of strings
        :param security_groups: The names of the EC2 classic security groups
            with which to associate instances

        :type user_data: string
        :param user_data: The user data passed to the launched instances

        :type instance_type: string
        :param instance_type: The type of instance to run:

            * t1.micro
            * m1.small
            * m1.medium
            * m1.large
            * m1.xlarge
            * m3.medium
            * m3.large
            * m3.xlarge
            * m3.2xlarge
            * c1.medium
            * c1.xlarge
            * m2.xlarge
            * m2.2xlarge
            * m2.4xlarge
            * cr1.8xlarge
            * hi1.4xlarge
            * hs1.8xlarge
            * cc1.4xlarge
            * cg1.4xlarge
            * cc2.8xlarge
            * g2.2xlarge
            * c3.large
            * c3.xlarge
            * c3.2xlarge
            * c3.4xlarge
            * c3.8xlarge
            * c4.large
            * c4.xlarge
            * c4.2xlarge
            * c4.4xlarge
            * c4.8xlarge
            * i2.xlarge
            * i2.2xlarge
            * i2.4xlarge
            * i2.8xlarge
            * t2.micro
            * t2.small
            * t2.medium

        :type placement: string
        :param placement: The Availability Zone to launch the instance into.

        :type kernel_id: string
        :param kernel_id: The ID of the kernel with which to launch the
            instances.

        :type ramdisk_id: string
        :param ramdisk_id: The ID of the RAM disk with which to launch the
            instances.

        :type monitoring_enabled: bool
        :param monitoring_enabled: Enable detailed CloudWatch monitoring on
            the instance.

        :type subnet_id: string
        :param subnet_id: The subnet ID within which to launch the instances
            for VPC.

        :type private_ip_address: string
        :param private_ip_address: If you're using VPC, you can
            optionally use this parameter to assign the instance a
            specific available IP address from the subnet (e.g.,
            10.0.0.25).

        :type block_device_map: :class:`boto.ec2.blockdevicemapping.BlockDeviceMapping`
        :param block_device_map: A BlockDeviceMapping data structure
            describing the EBS volumes associated with the Image.

        :type disable_api_termination: bool
        :param disable_api_termination: If True, the instances will be locked
            and will not be able to be terminated via the API.

        :type instance_initiated_shutdown_behavior: string
        :param instance_initiated_shutdown_behavior: Specifies whether the
            instance stops or terminates on instance-initiated shutdown.
            Valid values are:

            * stop
            * terminate

        :type placement_group: string
        :param placement_group: If specified, this is the name of the placement
            group in which the instance(s) will be launched.

        :type client_token: string
        :param client_token: Unique, case-sensitive identifier you provide
            to ensure idempotency of the request. Maximum 64 ASCII characters.

        :type security_group_ids: list of strings
        :param security_group_ids: The ID of the VPC security groups with
            which to associate instances.

        :type additional_info: string
        :param additional_info: Specifies additional information to make
            available to the instance(s).

        :type tenancy: string
        :param tenancy: The tenancy of the instance you want to
            launch. An instance with a tenancy of 'dedicated' runs on
            single-tenant hardware and can only be launched into a
            VPC. Valid values are:"default" or "dedicated".
            NOTE: To use dedicated tenancy you MUST specify a VPC
            subnet-ID as well.

        :type instance_profile_arn: string
        :param instance_profile_arn: The Amazon resource name (ARN) of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type instance_profile_name: string
        :param instance_profile_name: The name of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type ebs_optimized: bool
        :param ebs_optimized: Whether the instance is optimized for
            EBS I/O.  This optimization provides dedicated throughput
            to Amazon EBS and an optimized configuration stack to
            provide optimal EBS I/O performance.  This optimization
            isn't available with all instance types.

        :type network_interfaces: :class:`boto.ec2.networkinterface.NetworkInterfaceCollection`
        :param network_interfaces: A NetworkInterfaceCollection data
            structure containing the ENI specifications for the instance.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Reservation
        :return: The :class:`boto.ec2.instance.Reservation` associated with
                 the request for machines
        """
        params = {'ImageId': image_id,
                  'MinCount': min_count,
                  'MaxCount': max_count}
        if key_name:
            params['KeyName'] = key_name
        if security_group_ids:
            l = []
            for group in security_group_ids:
                if isinstance(group, SecurityGroup):
                    l.append(group.id)
                else:
                    l.append(group)
            self.build_list_params(params, l, 'SecurityGroupId')
        if security_groups:
            l = []
            for group in security_groups:
                if isinstance(group, SecurityGroup):
                    l.append(group.name)
                else:
                    l.append(group)
            self.build_list_params(params, l, 'SecurityGroup')
        if user_data:
            if isinstance(user_data, six.text_type):
                user_data = user_data.encode('utf-8')
            params['UserData'] = base64.b64encode(user_data).decode('utf-8')
        if addressing_type:
            params['AddressingType'] = addressing_type
        if instance_type:
            params['InstanceType'] = instance_type
        if placement:
            params['Placement.AvailabilityZone'] = placement
        if placement_group:
            params['Placement.GroupName'] = placement_group
        if tenancy:
            params['Placement.Tenancy'] = tenancy
        if kernel_id:
            params['KernelId'] = kernel_id
        if ramdisk_id:
            params['RamdiskId'] = ramdisk_id
        if monitoring_enabled:
            params['Monitoring.Enabled'] = 'true'
        if subnet_id:
            params['SubnetId'] = subnet_id
        if private_ip_address:
            params['PrivateIpAddress'] = private_ip_address
        if block_device_map:
            block_device_map.ec2_build_list_params(params)
        if disable_api_termination:
            params['DisableApiTermination'] = 'true'
        if instance_initiated_shutdown_behavior:
            val = instance_initiated_shutdown_behavior
            params['InstanceInitiatedShutdownBehavior'] = val
        if client_token:
            params['ClientToken'] = client_token
        if additional_info:
            params['AdditionalInfo'] = additional_info
        if instance_profile_name:
            params['IamInstanceProfile.Name'] = instance_profile_name
        if instance_profile_arn:
            params['IamInstanceProfile.Arn'] = instance_profile_arn
        if ebs_optimized:
            params['EbsOptimized'] = 'true'
        if network_interfaces:
            network_interfaces.build_list_params(params)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('RunInstances', params, Reservation,
                               verb='POST')

    def terminate_instances(self, instance_ids=None, dry_run=False):
        """
        Terminate the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to terminate

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of the instances terminated
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('TerminateInstances', params,
                             [('item', Instance)], verb='POST')

    def stop_instances(self, instance_ids=None, force=False, dry_run=False):
        """
        Stop the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to stop

        :type force: bool
        :param force: Forces the instance to stop

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of the instances stopped
        """
        params = {}
        if force:
            params['Force'] = 'true'
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('StopInstances', params,
                             [('item', Instance)], verb='POST')

    def start_instances(self, instance_ids=None, dry_run=False):
        """
        Start the instances specified

        :type instance_ids: list
        :param instance_ids: A list of strings of the Instance IDs to start

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of the instances started
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('StartInstances', params,
                             [('item', Instance)], verb='POST')

    def get_console_output(self, instance_id, dry_run=False):
        """
        Retrieves the console output for the specified instance.

        :type instance_id: string
        :param instance_id: The instance ID of a running instance on the cloud.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.instance.ConsoleOutput`
        :return: The console output as a ConsoleOutput object
        """
        params = {}
        self.build_list_params(params, [instance_id], 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('GetConsoleOutput', params,
                               ConsoleOutput, verb='POST')

    def reboot_instances(self, instance_ids=None, dry_run=False):
        """
        Reboot the specified instances.

        :type instance_ids: list
        :param instance_ids: The instances to terminate and reboot

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('RebootInstances', params)

    def confirm_product_instance(self, product_code, instance_id,
                                 dry_run=False):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'ProductCode': product_code,
                  'InstanceId': instance_id}
        if dry_run:
            params['DryRun'] = 'true'
        rs = self.get_object('ConfirmProductInstance', params,
                             ResultSet, verb='POST')
        return (rs.status, rs.ownerId)

    # InstanceAttribute methods

    def get_instance_attribute(self, instance_id, attribute, dry_run=False):
        """
        Gets an attribute from an instance.

        :type instance_id: string
        :param instance_id: The Amazon id of the instance

        :type attribute: string
        :param attribute: The attribute you need information about
            Valid choices are:

            * instanceType
            * kernel
            * ramdisk
            * userData
            * disableApiTermination
            * instanceInitiatedShutdownBehavior
            * rootDeviceName
            * blockDeviceMapping
            * productCodes
            * sourceDestCheck
            * groupSet
            * ebsOptimized
            * sriovNetSupport

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.image.InstanceAttribute`
        :return: An InstanceAttribute object representing the value of the
                 attribute requested
        """
        params = {'InstanceId': instance_id}
        if attribute:
            params['Attribute'] = attribute
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeInstanceAttribute', params,
                               InstanceAttribute, verb='POST')

    def modify_network_interface_attribute(self, interface_id, attr, value,
                                           attachment_id=None, dry_run=False):
        """
        Changes an attribute of a network interface.

        :type interface_id: string
        :param interface_id: The interface id. Looks like 'eni-xxxxxxxx'

        :type attr: string
        :param attr: The attribute you wish to change.

            Learn more at http://docs.aws.amazon.com/AWSEC2/latest/API\
            Reference/ApiReference-query-ModifyNetworkInterfaceAttribute.html

            * description - Textual description of interface
            * groupSet - List of security group ids or group objects
            * sourceDestCheck - Boolean
            * deleteOnTermination - Boolean. Must also specify attachment_id

        :type value: string
        :param value: The new value for the attribute

        :rtype: bool
        :return: Whether the operation succeeded or not

        :type attachment_id: string
        :param attachment_id: If you're modifying DeleteOnTermination you must
            specify the attachment_id.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        bool_reqs = (
            'deleteontermination',
            'sourcedestcheck',
        )
        if attr.lower() in bool_reqs:
            if isinstance(value, bool):
                if value:
                    value = 'true'
                else:
                    value = 'false'
            elif value not in ['true', 'false']:
                raise ValueError('%s must be a boolean, "true", or "false"!'
                                 % attr)

        params = {'NetworkInterfaceId': interface_id}

        # groupSet is handled differently from other arguments
        if attr.lower() == 'groupset':
            for idx, sg in enumerate(value):
                if isinstance(sg, SecurityGroup):
                    sg = sg.id
                params['SecurityGroupId.%s' % (idx + 1)] = sg
        elif attr.lower() == 'description':
            params['Description.Value'] = value
        elif attr.lower() == 'sourcedestcheck':
            params['SourceDestCheck.Value'] = value
        elif attr.lower() == 'deleteontermination':
            params['Attachment.DeleteOnTermination'] = value
            if not attachment_id:
                raise ValueError('You must also specify an attachment_id')
            params['Attachment.AttachmentId'] = attachment_id
        else:
            raise ValueError('Unknown attribute "%s"' % (attr,))

        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status(
            'ModifyNetworkInterfaceAttribute', params, verb='POST')

    def modify_instance_attribute(self, instance_id, attribute, value,
                                  dry_run=False):
        """
        Changes an attribute of an instance

        :type instance_id: string
        :param instance_id: The instance id you wish to change

        :type attribute: string
        :param attribute: The attribute you wish to change.

            * instanceType - A valid instance type (m1.small)
            * kernel - Kernel ID (None)
            * ramdisk - Ramdisk ID (None)
            * userData - Base64 encoded String (None)
            * disableApiTermination - Boolean (true)
            * instanceInitiatedShutdownBehavior - stop|terminate
            * blockDeviceMapping - List of strings - ie: ['/dev/sda=false']
            * sourceDestCheck - Boolean (true)
            * groupSet - Set of Security Groups or IDs
            * ebsOptimized - Boolean (false)
            * sriovNetSupport - String - ie: 'simple'

        :type value: string
        :param value: The new value for the attribute

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        # Allow a bool to be passed in for value of disableApiTermination
        bool_reqs = ('disableapitermination',
                     'sourcedestcheck',
                     'ebsoptimized')
        if attribute.lower() in bool_reqs:
            if isinstance(value, bool):
                if value:
                    value = 'true'
                else:
                    value = 'false'

        params = {'InstanceId': instance_id}

        # groupSet is handled differently from other arguments
        if attribute.lower() == 'groupset':
            for idx, sg in enumerate(value):
                if isinstance(sg, SecurityGroup):
                    sg = sg.id
                params['GroupId.%s' % (idx + 1)] = sg
        elif attribute.lower() == 'blockdevicemapping':
            for idx, kv in enumerate(value):
                dev_name, _, flag = kv.partition('=')
                pre = 'BlockDeviceMapping.%d' % (idx + 1)
                params['%s.DeviceName' % pre] = dev_name
                params['%s.Ebs.DeleteOnTermination' % pre] = flag or 'true'
        else:
            # for backwards compatibility handle lowercase first letter
            attribute = attribute[0].upper() + attribute[1:]
            params['%s.Value' % attribute] = value

        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifyInstanceAttribute', params, verb='POST')

    def reset_instance_attribute(self, instance_id, attribute, dry_run=False):
        """
        Resets an attribute of an instance to its default value.

        :type instance_id: string
        :param instance_id: ID of the instance

        :type attribute: string
        :param attribute: The attribute to reset. Valid values are:
                          kernel|ramdisk

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        params = {'InstanceId': instance_id,
                  'Attribute': attribute}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ResetInstanceAttribute', params, verb='POST')

    # Spot Instances

    def get_all_spot_instance_requests(self, request_ids=None,
                                       filters=None, dry_run=False):
        """
        Retrieve all the spot instances requests associated with your account.

        :type request_ids: list
        :param request_ids: A list of strings of spot instance request IDs

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of
                 :class:`boto.ec2.spotinstancerequest.SpotInstanceRequest`
        """
        params = {}
        if request_ids:
            self.build_list_params(params, request_ids, 'SpotInstanceRequestId')
        if filters:
            if 'launch.group-id' in filters:
                lgid = filters.get('launch.group-id')
                if not lgid.startswith('sg-') or len(lgid) != 11:
                    warnings.warn(
                        "The 'launch.group-id' filter now requires a security "
                        "group id (sg-*) and no longer supports filtering by "
                        "group name. Please update your filters accordingly.",
                        UserWarning)
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeSpotInstanceRequests', params,
                             [('item', SpotInstanceRequest)], verb='POST')

    def get_spot_price_history(self, start_time=None, end_time=None,
                               instance_type=None, product_description=None,
                               availability_zone=None, dry_run=False,
                               max_results=None, next_token=None,
                               filters=None):
        """
        Retrieve the recent history of spot instances pricing.

        :type start_time: str
        :param start_time: An indication of how far back to provide price
            changes for. An ISO8601 DateTime string.

        :type end_time: str
        :param end_time: An indication of how far forward to provide price
            changes for.  An ISO8601 DateTime string.

        :type instance_type: str
        :param instance_type: Filter responses to a particular instance type.

        :type product_description: str
        :param product_description: Filter responses to a particular platform.
            Valid values are currently:

            * Linux/UNIX
            * SUSE Linux
            * Windows
            * Linux/UNIX (Amazon VPC)
            * SUSE Linux (Amazon VPC)
            * Windows (Amazon VPC)

        :type availability_zone: str
        :param availability_zone: The availability zone for which prices
            should be returned.  If not specified, data for all
            availability zones will be returned.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated items
            per response.

        :type next_token: str
        :param next_token: The next set of rows to return.  This should
            be the value of the ``next_token`` attribute from a previous
            call to ``get_spot_price_history``.

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :rtype: list
        :return: A list tuples containing price and timestamp.
        """
        params = {}
        if start_time:
            params['StartTime'] = start_time
        if end_time:
            params['EndTime'] = end_time
        if instance_type:
            params['InstanceType'] = instance_type
        if product_description:
            params['ProductDescription'] = product_description
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if dry_run:
            params['DryRun'] = 'true'
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeSpotPriceHistory', params,
                             [('item', SpotPriceHistory)], verb='POST')

    def request_spot_instances(self, price, image_id, count=1, type='one-time',
                               valid_from=None, valid_until=None,
                               launch_group=None, availability_zone_group=None,
                               key_name=None, security_groups=None,
                               user_data=None, addressing_type=None,
                               instance_type='m1.small', placement=None,
                               kernel_id=None, ramdisk_id=None,
                               monitoring_enabled=False, subnet_id=None,
                               placement_group=None,
                               block_device_map=None,
                               instance_profile_arn=None,
                               instance_profile_name=None,
                               security_group_ids=None,
                               ebs_optimized=False,
                               network_interfaces=None, dry_run=False):
        """
        Request instances on the spot market at a particular price.

        :type price: str
        :param price: The maximum price of your bid

        :type image_id: string
        :param image_id: The ID of the image to run

        :type count: int
        :param count: The of instances to requested

        :type type: str
        :param type: Type of request. Can be 'one-time' or 'persistent'.
                     Default is one-time.

        :type valid_from: str
        :param valid_from: Start date of the request. An ISO8601 time string.

        :type valid_until: str
        :param valid_until: End date of the request.  An ISO8601 time string.

        :type launch_group: str
        :param launch_group: If supplied, all requests will be fulfilled
            as a group.

        :type availability_zone_group: str
        :param availability_zone_group: If supplied, all requests will be
            fulfilled within a single availability zone.

        :type key_name: string
        :param key_name: The name of the key pair with which to
            launch instances

        :type security_groups: list of strings
        :param security_groups: The names of the security groups with which to
            associate instances

        :type user_data: string
        :param user_data: The user data passed to the launched instances

        :type instance_type: string
        :param instance_type: The type of instance to run:

            * t1.micro
            * m1.small
            * m1.medium
            * m1.large
            * m1.xlarge
            * m3.medium
            * m3.large
            * m3.xlarge
            * m3.2xlarge
            * c1.medium
            * c1.xlarge
            * m2.xlarge
            * m2.2xlarge
            * m2.4xlarge
            * cr1.8xlarge
            * hi1.4xlarge
            * hs1.8xlarge
            * cc1.4xlarge
            * cg1.4xlarge
            * cc2.8xlarge
            * g2.2xlarge
            * c3.large
            * c3.xlarge
            * c3.2xlarge
            * c3.4xlarge
            * c3.8xlarge
            * c4.large
            * c4.xlarge
            * c4.2xlarge
            * c4.4xlarge
            * c4.8xlarge
            * i2.xlarge
            * i2.2xlarge
            * i2.4xlarge
            * i2.8xlarge
            * t2.micro
            * t2.small
            * t2.medium

        :type placement: string
        :param placement: The availability zone in which to launch
            the instances

        :type kernel_id: string
        :param kernel_id: The ID of the kernel with which to launch the
            instances

        :type ramdisk_id: string
        :param ramdisk_id: The ID of the RAM disk with which to launch the
            instances

        :type monitoring_enabled: bool
        :param monitoring_enabled: Enable detailed CloudWatch monitoring on
            the instance.

        :type subnet_id: string
        :param subnet_id: The subnet ID within which to launch the instances
            for VPC.

        :type placement_group: string
        :param placement_group: If specified, this is the name of the placement
            group in which the instance(s) will be launched.

        :type block_device_map: :class:`boto.ec2.blockdevicemapping.BlockDeviceMapping`
        :param block_device_map: A BlockDeviceMapping data structure
            describing the EBS volumes associated with the Image.

        :type security_group_ids: list of strings
        :param security_group_ids: The ID of the VPC security groups with
            which to associate instances.

        :type instance_profile_arn: string
        :param instance_profile_arn: The Amazon resource name (ARN) of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type instance_profile_name: string
        :param instance_profile_name: The name of
            the IAM Instance Profile (IIP) to associate with the instances.

        :type ebs_optimized: bool
        :param ebs_optimized: Whether the instance is optimized for
            EBS I/O.  This optimization provides dedicated throughput
            to Amazon EBS and an optimized configuration stack to
            provide optimal EBS I/O performance.  This optimization
            isn't available with all instance types.

        :type network_interfaces: list
        :param network_interfaces: A list of
            :class:`boto.ec2.networkinterface.NetworkInterfaceSpecification`

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: Reservation
        :return: The :class:`boto.ec2.spotinstancerequest.SpotInstanceRequest`
                 associated with the request for machines
        """
        ls = 'LaunchSpecification'
        params = {'%s.ImageId' % ls: image_id,
                  'Type': type,
                  'SpotPrice': price}
        if count:
            params['InstanceCount'] = count
        if valid_from:
            params['ValidFrom'] = valid_from
        if valid_until:
            params['ValidUntil'] = valid_until
        if launch_group:
            params['LaunchGroup'] = launch_group
        if availability_zone_group:
            params['AvailabilityZoneGroup'] = availability_zone_group
        if key_name:
            params['%s.KeyName' % ls] = key_name
        if security_group_ids:
            l = []
            for group in security_group_ids:
                if isinstance(group, SecurityGroup):
                    l.append(group.id)
                else:
                    l.append(group)
            self.build_list_params(params, l,
                                   '%s.SecurityGroupId' % ls)
        if security_groups:
            l = []
            for group in security_groups:
                if isinstance(group, SecurityGroup):
                    l.append(group.name)
                else:
                    l.append(group)
            self.build_list_params(params, l, '%s.SecurityGroup' % ls)
        if user_data:
            params['%s.UserData' % ls] = base64.b64encode(user_data)
        if addressing_type:
            params['%s.AddressingType' % ls] = addressing_type
        if instance_type:
            params['%s.InstanceType' % ls] = instance_type
        if placement:
            params['%s.Placement.AvailabilityZone' % ls] = placement
        if kernel_id:
            params['%s.KernelId' % ls] = kernel_id
        if ramdisk_id:
            params['%s.RamdiskId' % ls] = ramdisk_id
        if monitoring_enabled:
            params['%s.Monitoring.Enabled' % ls] = 'true'
        if subnet_id:
            params['%s.SubnetId' % ls] = subnet_id
        if placement_group:
            params['%s.Placement.GroupName' % ls] = placement_group
        if block_device_map:
            block_device_map.ec2_build_list_params(params, '%s.' % ls)
        if instance_profile_name:
            params['%s.IamInstanceProfile.Name' % ls] = instance_profile_name
        if instance_profile_arn:
            params['%s.IamInstanceProfile.Arn' % ls] = instance_profile_arn
        if ebs_optimized:
            params['%s.EbsOptimized' % ls] = 'true'
        if network_interfaces:
            network_interfaces.build_list_params(params, prefix=ls + '.')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('RequestSpotInstances', params,
                             [('item', SpotInstanceRequest)],
                             verb='POST')

    def cancel_spot_instance_requests(self, request_ids, dry_run=False):
        """
        Cancel the specified Spot Instance Requests.

        :type request_ids: list
        :param request_ids: A list of strings of the Request IDs to terminate

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of the instances terminated
        """
        params = {}
        if request_ids:
            self.build_list_params(params, request_ids, 'SpotInstanceRequestId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('CancelSpotInstanceRequests', params,
                             [('item', SpotInstanceRequest)], verb='POST')

    def get_spot_datafeed_subscription(self, dry_run=False):
        """
        Return the current spot instance data feed subscription
        associated with this account, if any.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.spotdatafeedsubscription.SpotDatafeedSubscription`
        :return: The datafeed subscription object or None
        """
        params = {}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeSpotDatafeedSubscription',
                               params, SpotDatafeedSubscription, verb='POST')

    def create_spot_datafeed_subscription(self, bucket, prefix, dry_run=False):
        """
        Create a spot instance datafeed subscription for this account.

        :type bucket: str or unicode
        :param bucket: The name of the bucket where spot instance data
                       will be written.  The account issuing this request
                       must have FULL_CONTROL access to the bucket
                       specified in the request.

        :type prefix: str or unicode
        :param prefix: An optional prefix that will be pre-pended to all
                       data files written to the bucket.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.spotdatafeedsubscription.SpotDatafeedSubscription`
        :return: The datafeed subscription object or None
        """
        params = {'Bucket': bucket}
        if prefix:
            params['Prefix'] = prefix
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateSpotDatafeedSubscription',
                               params, SpotDatafeedSubscription, verb='POST')

    def delete_spot_datafeed_subscription(self, dry_run=False):
        """
        Delete the current spot instance data feed subscription
        associated with this account

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteSpotDatafeedSubscription',
                               params, verb='POST')

    # Zone methods

    def get_all_zones(self, zones=None, filters=None, dry_run=False):
        """
        Get all Availability Zones associated with the current region.

        :type zones: list
        :param zones: Optional list of zones.  If this list is present,
                      only the Zones associated with these zone names
                      will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.zone.Zone`
        :return: The requested Zone objects
        """
        params = {}
        if zones:
            self.build_list_params(params, zones, 'ZoneName')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeAvailabilityZones', params,
                             [('item', Zone)], verb='POST')

    # Address methods

    def get_all_addresses(self, addresses=None, filters=None,
                          allocation_ids=None, dry_run=False):
        """
        Get all EIP's associated with the current credentials.

        :type addresses: list
        :param addresses: Optional list of addresses.  If this list is present,
                           only the Addresses associated with these addresses
                           will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type allocation_ids: list
        :param allocation_ids: Optional list of allocation IDs.  If this list is
                           present, only the Addresses associated with the given
                           allocation IDs will be returned.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.address.Address`
        :return: The requested Address objects
        """
        params = {}
        if addresses:
            self.build_list_params(params, addresses, 'PublicIp')
        if allocation_ids:
            self.build_list_params(params, allocation_ids, 'AllocationId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeAddresses', params, [('item', Address)], verb='POST')

    def allocate_address(self, domain=None, dry_run=False):
        """
        Allocate a new Elastic IP address and associate it with your account.

        :type domain: string
        :param domain: Optional string. If domain is set to "vpc" the address
            will be allocated to VPC . Will return address object with
            allocation_id.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.address.Address`
        :return: The newly allocated Address
        """
        params = {}

        if domain is not None:
            params['Domain'] = domain

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_object('AllocateAddress', params, Address, verb='POST')

    def assign_private_ip_addresses(self, network_interface_id=None,
                                    private_ip_addresses=None,
                                    secondary_private_ip_address_count=None,
                                    allow_reassignment=False, dry_run=False):
        """
        Assigns one or more secondary private IP addresses to a network
        interface in Amazon VPC.

        :type network_interface_id: string
        :param network_interface_id: The network interface to which the IP
            address will be assigned.

        :type private_ip_addresses: list
        :param private_ip_addresses: Assigns the specified IP addresses as
            secondary IP addresses to the network interface.

        :type secondary_private_ip_address_count: int
        :param secondary_private_ip_address_count: The number of secondary IP
            addresses to assign to the network interface. You cannot specify
            this parameter when also specifying private_ip_addresses.

        :type allow_reassignment: bool
        :param allow_reassignment: Specifies whether to allow an IP address
            that is already assigned to another network interface or instance
            to be reassigned to the specified network interface.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {}

        if network_interface_id is not None:
            params['NetworkInterfaceId'] = network_interface_id

        if private_ip_addresses is not None:
            self.build_list_params(params, private_ip_addresses,
                                   'PrivateIpAddress')
        elif secondary_private_ip_address_count is not None:
            params['SecondaryPrivateIpAddressCount'] = \
                secondary_private_ip_address_count

        if allow_reassignment:
            params['AllowReassignment'] = 'true'

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('AssignPrivateIpAddresses', params, verb='POST')

    def _associate_address(self, status, instance_id=None, public_ip=None,
                           allocation_id=None, network_interface_id=None,
                           private_ip_address=None, allow_reassociation=False,
                           dry_run=False):
        params = {}
        if instance_id is not None:
                params['InstanceId'] = instance_id
        elif network_interface_id is not None:
                params['NetworkInterfaceId'] = network_interface_id

        # Allocation id trumps public ip in order to associate with VPCs
        if allocation_id is not None:
            params['AllocationId'] = allocation_id
        elif public_ip is not None:
            params['PublicIp'] = public_ip

        if private_ip_address is not None:
            params['PrivateIpAddress'] = private_ip_address

        if allow_reassociation:
            params['AllowReassociation'] = 'true'

        if dry_run:
            params['DryRun'] = 'true'

        if status:
            return self.get_status('AssociateAddress', params, verb='POST')
        else:
            return self.get_object('AssociateAddress', params, Address,
                                   verb='POST')

    def associate_address(self, instance_id=None, public_ip=None,
                          allocation_id=None, network_interface_id=None,
                          private_ip_address=None, allow_reassociation=False,
                          dry_run=False):
        """
        Associate an Elastic IP address with a currently running instance.
        This requires one of ``public_ip`` or ``allocation_id`` depending
        on if you're associating a VPC address or a plain EC2 address.

        When using an Allocation ID, make sure to pass ``None`` for ``public_ip``
        as EC2 expects a single parameter and if ``public_ip`` is passed boto
        will preference that instead of ``allocation_id``.

        :type instance_id: string
        :param instance_id: The ID of the instance

        :type public_ip: string
        :param public_ip: The public IP address for EC2 based allocations.

        :type allocation_id: string
        :param allocation_id: The allocation ID for a VPC-based elastic IP.

        :type network_interface_id: string
        :param network_interface_id: The network interface ID to which
            elastic IP is to be assigned to

        :type private_ip_address: string
        :param private_ip_address: The primary or secondary private IP address
            to associate with the Elastic IP address.

        :type allow_reassociation: bool
        :param allow_reassociation: Specify this option to allow an Elastic IP
            address that is already associated with another network interface
            or instance to be re-associated with the specified instance or
            interface.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        return self._associate_address(True, instance_id=instance_id,
            public_ip=public_ip, allocation_id=allocation_id,
            network_interface_id=network_interface_id,
            private_ip_address=private_ip_address,
            allow_reassociation=allow_reassociation, dry_run=dry_run)

    def associate_address_object(self, instance_id=None, public_ip=None,
                                 allocation_id=None, network_interface_id=None,
                                 private_ip_address=None, allow_reassociation=False,
                                 dry_run=False):
        """
        Associate an Elastic IP address with a currently running instance.
        This requires one of ``public_ip`` or ``allocation_id`` depending
        on if you're associating a VPC address or a plain EC2 address.

        When using an Allocation ID, make sure to pass ``None`` for ``public_ip``
        as EC2 expects a single parameter and if ``public_ip`` is passed boto
        will preference that instead of ``allocation_id``.

        :type instance_id: string
        :param instance_id: The ID of the instance

        :type public_ip: string
        :param public_ip: The public IP address for EC2 based allocations.

        :type allocation_id: string
        :param allocation_id: The allocation ID for a VPC-based elastic IP.

        :type network_interface_id: string
        :param network_interface_id: The network interface ID to which
            elastic IP is to be assigned to

        :type private_ip_address: string
        :param private_ip_address: The primary or secondary private IP address
            to associate with the Elastic IP address.

        :type allow_reassociation: bool
        :param allow_reassociation: Specify this option to allow an Elastic IP
            address that is already associated with another network interface
            or instance to be re-associated with the specified instance or
            interface.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: class:`boto.ec2.address.Address`
        :return: The associated address instance
        """
        return self._associate_address(False, instance_id=instance_id,
            public_ip=public_ip, allocation_id=allocation_id,
            network_interface_id=network_interface_id,
            private_ip_address=private_ip_address,
            allow_reassociation=allow_reassociation, dry_run=dry_run)

    def disassociate_address(self, public_ip=None, association_id=None,
                             dry_run=False):
        """
        Disassociate an Elastic IP address from a currently running instance.

        :type public_ip: string
        :param public_ip: The public IP address for EC2 elastic IPs.

        :type association_id: string
        :param association_id: The association ID for a VPC based elastic ip.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {}

        # If there is an association id it trumps public ip
        # in order to successfully dissassociate with a VPC elastic ip
        if association_id is not None:
            params['AssociationId'] = association_id
        elif public_ip is not None:
            params['PublicIp'] = public_ip

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('DisassociateAddress', params, verb='POST')

    def release_address(self, public_ip=None, allocation_id=None,
                        dry_run=False):
        """
        Free up an Elastic IP address.  Pass a public IP address to
        release an EC2 Elastic IP address and an AllocationId to
        release a VPC Elastic IP address.  You should only pass
        one value.

        This requires one of ``public_ip`` or ``allocation_id`` depending
        on if you're associating a VPC address or a plain EC2 address.

        When using an Allocation ID, make sure to pass ``None`` for ``public_ip``
        as EC2 expects a single parameter and if ``public_ip`` is passed boto
        will preference that instead of ``allocation_id``.

        :type public_ip: string
        :param public_ip: The public IP address for EC2 elastic IPs.

        :type allocation_id: string
        :param allocation_id: The Allocation ID for VPC elastic IPs.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {}

        if public_ip is not None:
            params['PublicIp'] = public_ip
        elif allocation_id is not None:
            params['AllocationId'] = allocation_id

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('ReleaseAddress', params, verb='POST')

    def unassign_private_ip_addresses(self, network_interface_id=None,
                                      private_ip_addresses=None, dry_run=False):
        """
        Unassigns one or more secondary private IP addresses from a network
        interface in Amazon VPC.

        :type network_interface_id: string
        :param network_interface_id: The network interface from which the
            secondary private IP address will be unassigned.

        :type private_ip_addresses: list
        :param private_ip_addresses: Specifies the secondary private IP
            addresses that you want to unassign from the network interface.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {}

        if network_interface_id is not None:
            params['NetworkInterfaceId'] = network_interface_id

        if private_ip_addresses is not None:
            self.build_list_params(params, private_ip_addresses,
                                   'PrivateIpAddress')

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('UnassignPrivateIpAddresses', params,
                               verb='POST')

    # Volume methods

    def get_all_volumes(self, volume_ids=None, filters=None, dry_run=False):
        """
        Get all Volumes associated with the current credentials.

        :type volume_ids: list
        :param volume_ids: Optional list of volume ids.  If this list
                           is present, only the volumes associated with
                           these volume ids will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.volume.Volume`
        :return: The requested Volume objects
        """
        params = {}
        if volume_ids:
            self.build_list_params(params, volume_ids, 'VolumeId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeVolumes', params,
                             [('item', Volume)], verb='POST')

    def get_all_volume_status(self, volume_ids=None,
                              max_results=None, next_token=None,
                              filters=None, dry_run=False):
        """
        Retrieve the status of one or more volumes.

        :type volume_ids: list
        :param volume_ids: A list of strings of volume IDs

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :type next_token: str
        :param next_token: A string specifying the next paginated set
            of results to return.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
            the results returned.  Filters are provided
            in the form of a dictionary consisting of
            filter names as the key and filter values
            as the value.  The set of allowable filter
            names/values is dependent on the request
            being performed.  Check the EC2 API guide
            for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of volume status.
        """
        params = {}
        if volume_ids:
            self.build_list_params(params, volume_ids, 'VolumeId')
        if max_results:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeVolumeStatus', params,
                               VolumeStatusSet, verb='POST')

    def enable_volume_io(self, volume_id, dry_run=False):
        """
        Enables I/O operations for a volume that had I/O operations
        disabled because the data on the volume was potentially inconsistent.

        :type volume_id: str
        :param volume_id: The ID of the volume.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VolumeId': volume_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('EnableVolumeIO', params, verb='POST')

    def get_volume_attribute(self, volume_id,
                             attribute='autoEnableIO', dry_run=False):
        """
        Describes attribute of the volume.

        :type volume_id: str
        :param volume_id: The ID of the volume.

        :type attribute: str
        :param attribute: The requested attribute.  Valid values are:

            * autoEnableIO

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.volume.VolumeAttribute`
        :return: The requested Volume attribute
        """
        params = {'VolumeId': volume_id, 'Attribute': attribute}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeVolumeAttribute', params,
                               VolumeAttribute, verb='POST')

    def modify_volume_attribute(self, volume_id, attribute, new_value,
                                dry_run=False):
        """
        Changes an attribute of an Volume.

        :type volume_id: string
        :param volume_id: The volume id you wish to change

        :type attribute: string
        :param attribute: The attribute you wish to change.  Valid values are:
            AutoEnableIO.

        :type new_value: string
        :param new_value: The new value of the attribute.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'VolumeId': volume_id}
        if attribute == 'AutoEnableIO':
            params['AutoEnableIO.Value'] = new_value
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifyVolumeAttribute', params, verb='POST')

    def create_volume(self, size, zone, snapshot=None, volume_type=None,
                      iops=None, encrypted=False, kms_key_id=None, dry_run=False):
        """
        Create a new EBS Volume.

        :type size: int
        :param size: The size of the new volume, in GiB

        :type zone: string or :class:`boto.ec2.zone.Zone`
        :param zone: The availability zone in which the Volume will be created.

        :type snapshot: string or :class:`boto.ec2.snapshot.Snapshot`
        :param snapshot: The snapshot from which the new Volume will be
            created.

        :type volume_type: string
        :param volume_type: The type of the volume. (optional).  Valid
            values are: standard | io1 | gp2.

        :type iops: int
        :param iops: The provisioned IOPS you want to associate with
            this volume. (optional)

        :type encrypted: bool
        :param encrypted: Specifies whether the volume should be encrypted.
            (optional)

        :type kms_key_id: string
        :params kms_key_id: If encrypted is True, this KMS Key ID may be specified to
            encrypt volume with this key (optional)
            e.g.: arn:aws:kms:us-east-1:012345678910:key/abcd1234-a123-456a-a12b-a123b4cd56ef

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        if isinstance(zone, Zone):
            zone = zone.name
        params = {'AvailabilityZone': zone}
        if size:
            params['Size'] = size
        if snapshot:
            if isinstance(snapshot, Snapshot):
                snapshot = snapshot.id
            params['SnapshotId'] = snapshot
        if volume_type:
            params['VolumeType'] = volume_type
        if iops:
            params['Iops'] = str(iops)
        if encrypted:
            params['Encrypted'] = 'true'
            if kms_key_id:
                params['KmsKeyId'] = kms_key_id
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateVolume', params, Volume, verb='POST')

    def delete_volume(self, volume_id, dry_run=False):
        """
        Delete an EBS volume.

        :type volume_id: str
        :param volume_id: The ID of the volume to be delete.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VolumeId': volume_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteVolume', params, verb='POST')

    def attach_volume(self, volume_id, instance_id, device, dry_run=False):
        """
        Attach an EBS volume to an EC2 instance.

        :type volume_id: str
        :param volume_id: The ID of the EBS volume to be attached.

        :type instance_id: str
        :param instance_id: The ID of the EC2 instance to which it will
                            be attached.

        :type device: str
        :param device: The device on the instance through which the
                       volume will be exposted (e.g. /dev/sdh)

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'InstanceId': instance_id,
                  'VolumeId': volume_id,
                  'Device': device}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('AttachVolume', params, verb='POST')

    def detach_volume(self, volume_id, instance_id=None,
                      device=None, force=False, dry_run=False):
        """
        Detach an EBS volume from an EC2 instance.

        :type volume_id: str
        :param volume_id: The ID of the EBS volume to be attached.

        :type instance_id: str
        :param instance_id: The ID of the EC2 instance from which it will
            be detached.

        :type device: str
        :param device: The device on the instance through which the
            volume is exposted (e.g. /dev/sdh)

        :type force: bool
        :param force: Forces detachment if the previous detachment
            attempt did not occur cleanly.  This option can lead to
            data loss or a corrupted file system. Use this option only
            as a last resort to detach a volume from a failed
            instance. The instance will not have an opportunity to
            flush file system caches nor file system meta data. If you
            use this option, you must perform file system check and
            repair procedures.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'VolumeId': volume_id}
        if instance_id:
            params['InstanceId'] = instance_id
        if device:
            params['Device'] = device
        if force:
            params['Force'] = 'true'
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DetachVolume', params, verb='POST')

    # Snapshot methods

    def get_all_snapshots(self, snapshot_ids=None,
                          owner=None, restorable_by=None,
                          filters=None, dry_run=False):
        """
        Get all EBS Snapshots associated with the current credentials.

        :type snapshot_ids: list
        :param snapshot_ids: Optional list of snapshot ids.  If this list is
                             present, only the Snapshots associated with
                             these snapshot ids will be returned.

        :type owner: str or list
        :param owner: If present, only the snapshots owned by the specified user(s)
                      will be returned.  Valid values are:

                      * self
                      * amazon
                      * AWS Account ID

        :type restorable_by: str or list
        :param restorable_by: If present, only the snapshots that are restorable
                              by the specified account id(s) will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.snapshot.Snapshot`
        :return: The requested Snapshot objects
        """
        params = {}
        if snapshot_ids:
            self.build_list_params(params, snapshot_ids, 'SnapshotId')

        if owner:
            self.build_list_params(params, owner, 'Owner')
        if restorable_by:
            self.build_list_params(params, restorable_by, 'RestorableBy')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeSnapshots', params,
                             [('item', Snapshot)], verb='POST')

    def create_snapshot(self, volume_id, description=None, dry_run=False):
        """
        Create a snapshot of an existing EBS Volume.

        :type volume_id: str
        :param volume_id: The ID of the volume to be snapshot'ed

        :type description: str
        :param description: A description of the snapshot.
                            Limited to 255 characters.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.snapshot.Snapshot`
        :return: The created Snapshot object
        """
        params = {'VolumeId': volume_id}
        if description:
            params['Description'] = description[0:255]
        if dry_run:
            params['DryRun'] = 'true'
        snapshot = self.get_object('CreateSnapshot', params,
                                   Snapshot, verb='POST')
        volume = self.get_all_volumes([volume_id], dry_run=dry_run)[0]
        volume_name = volume.tags.get('Name')
        if volume_name:
            snapshot.add_tag('Name', volume_name)
        return snapshot

    def delete_snapshot(self, snapshot_id, dry_run=False):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'SnapshotId': snapshot_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteSnapshot', params, verb='POST')

    def copy_snapshot(self, source_region, source_snapshot_id,
                      description=None, dry_run=False):
        """
        Copies a point-in-time snapshot of an Amazon Elastic Block Store
        (Amazon EBS) volume and stores it in Amazon Simple Storage Service
        (Amazon S3). You can copy the snapshot within the same region or from
        one region to another. You can use the snapshot to create new Amazon
        EBS volumes or Amazon Machine Images (AMIs).


        :type source_region: str
        :param source_region: The ID of the AWS region that contains the
            snapshot to be copied (e.g 'us-east-1', 'us-west-2', etc.).

        :type source_snapshot_id: str
        :param source_snapshot_id: The ID of the Amazon EBS snapshot to copy

        :type description: str
        :param description: A description of the new Amazon EBS snapshot.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: str
        :return: The snapshot ID

        """
        params = {
            'SourceRegion': source_region,
            'SourceSnapshotId': source_snapshot_id,
        }
        if description is not None:
            params['Description'] = description
        if dry_run:
            params['DryRun'] = 'true'
        snapshot = self.get_object('CopySnapshot', params, Snapshot,
                                   verb='POST')
        return snapshot.id

    def trim_snapshots(self, hourly_backups=8, daily_backups=7,
                       weekly_backups=4, monthly_backups=True):
        """
        Trim excess snapshots, based on when they were taken. More current
        snapshots are retained, with the number retained decreasing as you
        move back in time.

        If ebs volumes have a 'Name' tag with a value, their snapshots
        will be assigned the same tag when they are created. The values
        of the 'Name' tags for snapshots are used by this function to
        group snapshots taken from the same volume (or from a series
        of like-named volumes over time) for trimming.

        For every group of like-named snapshots, this function retains
        the newest and oldest snapshots, as well as, by default,  the
        first snapshots taken in each of the last eight hours, the first
        snapshots taken in each of the last seven days, the first snapshots
        taken in the last 4 weeks (counting Midnight Sunday morning as
        the start of the week), and the first snapshot from the first
        day of each month forever.

        :type hourly_backups: int
        :param hourly_backups: How many recent hourly backups should be saved.

        :type daily_backups: int
        :param daily_backups: How many recent daily backups should be saved.

        :type weekly_backups: int
        :param weekly_backups: How many recent weekly backups should be saved.

        :type monthly_backups: int
        :param monthly_backups: How many monthly backups should be saved. Use True for no limit.
        """

        # This function first builds up an ordered list of target times
        # that snapshots should be saved for (last 8 hours, last 7 days, etc.).
        # Then a map of snapshots is constructed, with the keys being
        # the snapshot / volume names and the values being arrays of
        # chronologically sorted snapshots.
        # Finally, for each array in the map, we go through the snapshot
        # array and the target time array in an interleaved fashion,
        # deleting snapshots whose start_times don't immediately follow a
        # target time (we delete a snapshot if there's another snapshot
        # that was made closer to the preceding target time).

        now = datetime.utcnow()
        last_hour = datetime(now.year, now.month, now.day, now.hour)
        last_midnight = datetime(now.year, now.month, now.day)
        last_sunday = datetime(now.year, now.month, now.day) - timedelta(days=(now.weekday() + 1) % 7)
        start_of_month = datetime(now.year, now.month, 1)

        target_backup_times = []

        # there are no snapshots older than 1/1/2007
        oldest_snapshot_date = datetime(2007, 1, 1)

        for hour in range(0, hourly_backups):
            target_backup_times.append(last_hour - timedelta(hours=hour))

        for day in range(0, daily_backups):
            target_backup_times.append(last_midnight - timedelta(days=day))

        for week in range(0, weekly_backups):
            target_backup_times.append(last_sunday - timedelta(weeks=week))

        one_day = timedelta(days=1)
        monthly_snapshots_added = 0
        while (start_of_month > oldest_snapshot_date and
               (monthly_backups is True or
                monthly_snapshots_added < monthly_backups)):
            # append the start of the month to the list of
            # snapshot dates to save:
            target_backup_times.append(start_of_month)
            monthly_snapshots_added += 1
            # there's no timedelta setting for one month, so instead:
            # decrement the day by one, so we go to the final day of
            # the previous month...
            start_of_month -= one_day
            # ... and then go to the first day of that previous month:
            start_of_month = datetime(start_of_month.year,
                                      start_of_month.month, 1)

        temp = []

        for t in target_backup_times:
            if temp.__contains__(t) == False:
                temp.append(t)

        # sort to make the oldest dates first, and make sure the month start
        # and last four week's start are in the proper order
        target_backup_times = sorted(temp)

        # get all the snapshots, sort them by date and time, and
        # organize them into one array for each volume:
        all_snapshots = self.get_all_snapshots(owner = 'self')
        all_snapshots.sort(key=lambda x: x.start_time)
        snaps_for_each_volume = {}
        for snap in all_snapshots:
            # the snapshot name and the volume name are the same.
            # The snapshot name is set from the volume
            # name at the time the snapshot is taken
            volume_name = snap.tags.get('Name')
            if volume_name:
                # only examine snapshots that have a volume name
                snaps_for_volume = snaps_for_each_volume.get(volume_name)
                if not snaps_for_volume:
                    snaps_for_volume = []
                    snaps_for_each_volume[volume_name] = snaps_for_volume
                snaps_for_volume.append(snap)

        # Do a running comparison of snapshot dates to desired time
        #periods, keeping the oldest snapshot in each
        # time period and deleting the rest:
        for volume_name in snaps_for_each_volume:
            snaps = snaps_for_each_volume[volume_name]
            snaps = snaps[:-1] # never delete the newest snapshot
            time_period_number = 0
            snap_found_for_this_time_period = False
            for snap in snaps:
                check_this_snap = True
                while check_this_snap and time_period_number < target_backup_times.__len__():
                    snap_date = datetime.strptime(snap.start_time,
                                                  '%Y-%m-%dT%H:%M:%S.000Z')
                    if snap_date < target_backup_times[time_period_number]:
                        # the snap date is before the cutoff date.
                        # Figure out if it's the first snap in this
                        # date range and act accordingly (since both
                        #date the date ranges and the snapshots
                        # are sorted chronologically, we know this
                        #snapshot isn't in an earlier date range):
                        if snap_found_for_this_time_period == True:
                            if not snap.tags.get('preserve_snapshot'):
                                # as long as the snapshot wasn't marked
                                # with the 'preserve_snapshot' tag, delete it:
                                try:
                                    self.delete_snapshot(snap.id)
                                    boto.log.info('Trimmed snapshot %s (%s)' % (snap.tags['Name'], snap.start_time))
                                except EC2ResponseError:
                                    boto.log.error('Attempt to trim snapshot %s (%s) failed. Possible result of a race condition with trimming on another server?' % (snap.tags['Name'], snap.start_time))
                            # go on and look at the next snapshot,
                            #leaving the time period alone
                        else:
                            # this was the first snapshot found for this
                            #time period. Leave it alone and look at the
                            # next snapshot:
                            snap_found_for_this_time_period = True
                        check_this_snap = False
                    else:
                        # the snap is after the cutoff date. Check it
                        # against the next cutoff date
                        time_period_number += 1
                        snap_found_for_this_time_period = False

    def get_snapshot_attribute(self, snapshot_id,
                               attribute='createVolumePermission',
                               dry_run=False):
        """
        Get information about an attribute of a snapshot.  Only one attribute
        can be specified per call.

        :type snapshot_id: str
        :param snapshot_id: The ID of the snapshot.

        :type attribute: str
        :param attribute: The requested attribute.  Valid values are:

                          * createVolumePermission

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list of :class:`boto.ec2.snapshotattribute.SnapshotAttribute`
        :return: The requested Snapshot attribute
        """
        params = {'Attribute': attribute}
        if snapshot_id:
            params['SnapshotId'] = snapshot_id
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeSnapshotAttribute', params,
                               SnapshotAttribute, verb='POST')

    def modify_snapshot_attribute(self, snapshot_id,
                                  attribute='createVolumePermission',
                                  operation='add', user_ids=None, groups=None,
                                  dry_run=False):
        """
        Changes an attribute of an image.

        :type snapshot_id: string
        :param snapshot_id: The snapshot id you wish to change

        :type attribute: string
        :param attribute: The attribute you wish to change.  Valid values are:
            createVolumePermission

        :type operation: string
        :param operation: Either add or remove (this is required for changing
            snapshot ermissions)

        :type user_ids: list
        :param user_ids: The Amazon IDs of users to add/remove attributes

        :type groups: list
        :param groups: The groups to add/remove attributes.  The only valid
            value at this time is 'all'.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'SnapshotId': snapshot_id,
                  'Attribute': attribute,
                  'OperationType': operation}
        if user_ids:
            self.build_list_params(params, user_ids, 'UserId')
        if groups:
            self.build_list_params(params, groups, 'UserGroup')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifySnapshotAttribute', params, verb='POST')

    def reset_snapshot_attribute(self, snapshot_id,
                                 attribute='createVolumePermission',
                                 dry_run=False):
        """
        Resets an attribute of a snapshot to its default value.

        :type snapshot_id: string
        :param snapshot_id: ID of the snapshot

        :type attribute: string
        :param attribute: The attribute to reset

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: Whether the operation succeeded or not
        """
        params = {'SnapshotId': snapshot_id,
                  'Attribute': attribute}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ResetSnapshotAttribute', params, verb='POST')

    # Keypair methods

    def get_all_key_pairs(self, keynames=None, filters=None, dry_run=False):
        """
        Get all key pairs associated with your account.

        :type keynames: list
        :param keynames: A list of the names of keypairs to retrieve.
            If not provided, all key pairs will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.keypair.KeyPair`
        """
        params = {}
        if keynames:
            self.build_list_params(params, keynames, 'KeyName')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeKeyPairs', params,
                             [('item', KeyPair)], verb='POST')

    def get_key_pair(self, keyname, dry_run=False):
        """
        Convenience method to retrieve a specific keypair (KeyPair).

        :type keyname: string
        :param keyname: The name of the keypair to retrieve

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.keypair.KeyPair`
        :return: The KeyPair specified or None if it is not found
        """
        try:
            return self.get_all_key_pairs(
                keynames=[keyname],
                dry_run=dry_run
            )[0]
        except self.ResponseError as e:
            if e.code == 'InvalidKeyPair.NotFound':
                return None
            else:
                raise

    def create_key_pair(self, key_name, dry_run=False):
        """
        Create a new key pair for your account.
        This will create the key pair within the region you
        are currently connected to.

        :type key_name: string
        :param key_name: The name of the new keypair

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.keypair.KeyPair`
        :return: The newly created :class:`boto.ec2.keypair.KeyPair`.
                 The material attribute of the new KeyPair object
                 will contain the the unencrypted PEM encoded RSA private key.
        """
        params = {'KeyName': key_name}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateKeyPair', params, KeyPair, verb='POST')

    def delete_key_pair(self, key_name, dry_run=False):
        """
        Delete a key pair from your account.

        :type key_name: string
        :param key_name: The name of the keypair to delete

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'KeyName': key_name}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteKeyPair', params, verb='POST')

    def import_key_pair(self, key_name, public_key_material, dry_run=False):
        """
        imports the public key from an RSA key pair that you created
        with a third-party tool.

        Supported formats:

        * OpenSSH public key format (e.g., the format
          in ~/.ssh/authorized_keys)

        * Base64 encoded DER format

        * SSH public key file format as specified in RFC4716

        DSA keys are not supported. Make sure your key generator is
        set up to create RSA keys.

        Supported lengths: 1024, 2048, and 4096.

        :type key_name: string
        :param key_name: The name of the new keypair

        :type public_key_material: string
        :param public_key_material: The public key. You must base64 encode
                                    the public key material before sending
                                    it to AWS.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.keypair.KeyPair`
        :return: A :class:`boto.ec2.keypair.KeyPair` object representing
            the newly imported key pair.  This object will contain only
            the key name and the fingerprint.
        """
        public_key_material = base64.b64encode(public_key_material)
        params = {'KeyName': key_name,
                  'PublicKeyMaterial': public_key_material}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('ImportKeyPair', params, KeyPair, verb='POST')

    # SecurityGroup methods

    def get_all_security_groups(self, groupnames=None, group_ids=None,
                                filters=None, dry_run=False):
        """
        Get all security groups associated with your account in a region.

        :type groupnames: list
        :param groupnames: A list of the names of security groups to retrieve.
                           If not provided, all security groups will be
                           returned.

        :type group_ids: list
        :param group_ids: A list of IDs of security groups to retrieve for
                          security groups within a VPC.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.securitygroup.SecurityGroup`
        """
        params = {}
        if groupnames is not None:
            self.build_list_params(params, groupnames, 'GroupName')
        if group_ids is not None:
            self.build_list_params(params, group_ids, 'GroupId')
        if filters is not None:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeSecurityGroups', params,
                             [('item', SecurityGroup)], verb='POST')

    def create_security_group(self, name, description, vpc_id=None,
                              dry_run=False):
        """
        Create a new security group for your account.
        This will create the security group within the region you
        are currently connected to.

        :type name: string
        :param name: The name of the new security group

        :type description: string
        :param description: The description of the new security group

        :type vpc_id: string
        :param vpc_id: The ID of the VPC to create the security group in,
                       if any.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.securitygroup.SecurityGroup`
        :return: The newly created :class:`boto.ec2.securitygroup.SecurityGroup`.
        """
        params = {'GroupName': name,
                  'GroupDescription': description}

        if vpc_id is not None:
            params['VpcId'] = vpc_id

        if dry_run:
            params['DryRun'] = 'true'

        group = self.get_object('CreateSecurityGroup', params,
                                SecurityGroup, verb='POST')
        group.name = name
        group.description = description
        if vpc_id is not None:
            group.vpc_id = vpc_id
        return group

    def delete_security_group(self, name=None, group_id=None, dry_run=False):
        """
        Delete a security group from your account.

        :type name: string
        :param name: The name of the security group to delete.

        :type group_id: string
        :param group_id: The ID of the security group to delete within
          a VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """
        params = {}

        if name is not None:
            params['GroupName'] = name
        elif group_id is not None:
            params['GroupId'] = group_id

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('DeleteSecurityGroup', params, verb='POST')

    def authorize_security_group_deprecated(self, group_name,
                                            src_security_group_name=None,
                                            src_security_group_owner_id=None,
                                            ip_protocol=None,
                                            from_port=None, to_port=None,
                                            cidr_ip=None, dry_run=False):
        """
        NOTE: This method uses the old-style request parameters
              that did not allow a port to be specified when
              authorizing a group.

        :type group_name: string
        :param group_name: The name of the security group you are adding
            the rule to.

        :type src_security_group_name: string
        :param src_security_group_name: The name of the security group you are
            granting access to.

        :type src_security_group_owner_id: string
        :param src_security_group_owner_id: The ID of the owner of the security
            group you are granting access to.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type to_port: string
        :param to_port: The CIDR block you are providing access to.
            See http://goo.gl/Yj5QC

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """
        params = {'GroupName': group_name}
        if src_security_group_name:
            params['SourceSecurityGroupName'] = src_security_group_name
        if src_security_group_owner_id:
            params['SourceSecurityGroupOwnerId'] = src_security_group_owner_id
        if ip_protocol:
            params['IpProtocol'] = ip_protocol
        if from_port:
            params['FromPort'] = from_port
        if to_port:
            params['ToPort'] = to_port
        if cidr_ip:
            params['CidrIp'] = cidr_ip
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('AuthorizeSecurityGroupIngress', params)

    def authorize_security_group(self, group_name=None,
                                 src_security_group_name=None,
                                 src_security_group_owner_id=None,
                                 ip_protocol=None,
                                 from_port=None, to_port=None,
                                 cidr_ip=None, group_id=None,
                                 src_security_group_group_id=None,
                                 dry_run=False):
        """
        Add a new rule to an existing security group.
        You need to pass in either src_security_group_name and
        src_security_group_owner_id OR ip_protocol, from_port, to_port,
        and cidr_ip.  In other words, either you are authorizing another
        group or you are authorizing some ip-based rule.

        :type group_name: string
        :param group_name: The name of the security group you are adding
            the rule to.

        :type src_security_group_name: string
        :param src_security_group_name: The name of the security group you are
            granting access to.

        :type src_security_group_owner_id: string
        :param src_security_group_owner_id: The ID of the owner of the security
            group you are granting access to.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type cidr_ip: string or list of strings
        :param cidr_ip: The CIDR block you are providing access to.
            See http://goo.gl/Yj5QC

        :type group_id: string
        :param group_id: ID of the EC2 or VPC security group to
            modify.  This is required for VPC security groups and can
            be used instead of group_name for EC2 security groups.

        :type src_security_group_group_id: string
        :param src_security_group_group_id: The ID of the security
            group you are granting access to.  Can be used instead of
            src_security_group_name

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """
        if src_security_group_name:
            if from_port is None and to_port is None and ip_protocol is None:
                return self.authorize_security_group_deprecated(
                    group_name, src_security_group_name,
                    src_security_group_owner_id)

        params = {}

        if group_name:
            params['GroupName'] = group_name
        if group_id:
            params['GroupId'] = group_id
        if src_security_group_name:
            param_name = 'IpPermissions.1.Groups.1.GroupName'
            params[param_name] = src_security_group_name
        if src_security_group_owner_id:
            param_name = 'IpPermissions.1.Groups.1.UserId'
            params[param_name] = src_security_group_owner_id
        if src_security_group_group_id:
            param_name = 'IpPermissions.1.Groups.1.GroupId'
            params[param_name] = src_security_group_group_id
        if ip_protocol:
            params['IpPermissions.1.IpProtocol'] = ip_protocol
        if from_port is not None:
            params['IpPermissions.1.FromPort'] = from_port
        if to_port is not None:
            params['IpPermissions.1.ToPort'] = to_port
        if cidr_ip:
            if not isinstance(cidr_ip, list):
                cidr_ip = [cidr_ip]
            for i, single_cidr_ip in enumerate(cidr_ip):
                params['IpPermissions.1.IpRanges.%d.CidrIp' % (i + 1)] = \
                    single_cidr_ip
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('AuthorizeSecurityGroupIngress',
                               params, verb='POST')

    def authorize_security_group_egress(self,
                                        group_id,
                                        ip_protocol,
                                        from_port=None,
                                        to_port=None,
                                        src_group_id=None,
                                        cidr_ip=None,
                                        dry_run=False):
        """
        The action adds one or more egress rules to a VPC security
        group. Specifically, this action permits instances in a
        security group to send traffic to one or more destination
        CIDR IP address ranges, or to one or more destination
        security groups in the same VPC.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {
            'GroupId': group_id,
            'IpPermissions.1.IpProtocol': ip_protocol
        }

        if from_port is not None:
            params['IpPermissions.1.FromPort'] = from_port
        if to_port is not None:
            params['IpPermissions.1.ToPort'] = to_port
        if src_group_id is not None:
            params['IpPermissions.1.Groups.1.GroupId'] = src_group_id
        if cidr_ip is not None:
            params['IpPermissions.1.IpRanges.1.CidrIp'] = cidr_ip
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_status('AuthorizeSecurityGroupEgress',
                               params, verb='POST')

    def revoke_security_group_deprecated(self, group_name,
                                         src_security_group_name=None,
                                         src_security_group_owner_id=None,
                                         ip_protocol=None,
                                         from_port=None, to_port=None,
                                         cidr_ip=None, dry_run=False):
        """
        NOTE: This method uses the old-style request parameters
              that did not allow a port to be specified when
              authorizing a group.

        Remove an existing rule from an existing security group.
        You need to pass in either src_security_group_name and
        src_security_group_owner_id OR ip_protocol, from_port, to_port,
        and cidr_ip.  In other words, either you are revoking another
        group or you are revoking some ip-based rule.

        :type group_name: string
        :param group_name: The name of the security group you are removing
                           the rule from.

        :type src_security_group_name: string
        :param src_security_group_name: The name of the security group you are
                                        revoking access to.

        :type src_security_group_owner_id: string
        :param src_security_group_owner_id: The ID of the owner of the security
                                            group you are revoking access to.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp

        :type from_port: int
        :param from_port: The beginning port number you are disabling

        :type to_port: int
        :param to_port: The ending port number you are disabling

        :type to_port: string
        :param to_port: The CIDR block you are revoking access to.
                        http://goo.gl/Yj5QC

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """
        params = {'GroupName': group_name}
        if src_security_group_name:
            params['SourceSecurityGroupName'] = src_security_group_name
        if src_security_group_owner_id:
            params['SourceSecurityGroupOwnerId'] = src_security_group_owner_id
        if ip_protocol:
            params['IpProtocol'] = ip_protocol
        if from_port:
            params['FromPort'] = from_port
        if to_port:
            params['ToPort'] = to_port
        if cidr_ip:
            params['CidrIp'] = cidr_ip
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('RevokeSecurityGroupIngress', params)

    def revoke_security_group(self, group_name=None,
                              src_security_group_name=None,
                              src_security_group_owner_id=None,
                              ip_protocol=None, from_port=None, to_port=None,
                              cidr_ip=None, group_id=None,
                              src_security_group_group_id=None, dry_run=False):
        """
        Remove an existing rule from an existing security group.
        You need to pass in either src_security_group_name and
        src_security_group_owner_id OR ip_protocol, from_port, to_port,
        and cidr_ip.  In other words, either you are revoking another
        group or you are revoking some ip-based rule.

        :type group_name: string
        :param group_name: The name of the security group you are removing
            the rule from.

        :type src_security_group_name: string
        :param src_security_group_name: The name of the security group you are
            revoking access to.

        :type src_security_group_owner_id: string
        :param src_security_group_owner_id: The ID of the owner of the security
            group you are revoking access to.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp

        :type from_port: int
        :param from_port: The beginning port number you are disabling

        :type to_port: int
        :param to_port: The ending port number you are disabling

        :type cidr_ip: string
        :param cidr_ip: The CIDR block you are revoking access to.
            See http://goo.gl/Yj5QC

        :type group_id: string
        :param group_id: ID of the EC2 or VPC security group to
            modify.  This is required for VPC security groups and can
            be used instead of group_name for EC2 security groups.

        :type src_security_group_group_id: string
        :param src_security_group_group_id: The ID of the security group
            for which you are revoking access.  Can be used instead
            of src_security_group_name

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """
        if src_security_group_name:
            if from_port is None and to_port is None and ip_protocol is None:
                return self.revoke_security_group_deprecated(
                    group_name, src_security_group_name,
                    src_security_group_owner_id)
        params = {}
        if group_name is not None:
            params['GroupName'] = group_name
        if group_id is not None:
            params['GroupId'] = group_id
        if src_security_group_name:
            param_name = 'IpPermissions.1.Groups.1.GroupName'
            params[param_name] = src_security_group_name
        if src_security_group_group_id:
            param_name = 'IpPermissions.1.Groups.1.GroupId'
            params[param_name] = src_security_group_group_id
        if src_security_group_owner_id:
            param_name = 'IpPermissions.1.Groups.1.UserId'
            params[param_name] = src_security_group_owner_id
        if ip_protocol:
            params['IpPermissions.1.IpProtocol'] = ip_protocol
        if from_port is not None:
            params['IpPermissions.1.FromPort'] = from_port
        if to_port is not None:
            params['IpPermissions.1.ToPort'] = to_port
        if cidr_ip:
            params['IpPermissions.1.IpRanges.1.CidrIp'] = cidr_ip
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('RevokeSecurityGroupIngress',
                               params, verb='POST')

    def revoke_security_group_egress(self,
                                     group_id,
                                     ip_protocol,
                                     from_port=None,
                                     to_port=None,
                                     src_group_id=None,
                                     cidr_ip=None, dry_run=False):
        """
        Remove an existing egress rule from an existing VPC security
        group.  You need to pass in an ip_protocol, from_port and
        to_port range only if the protocol you are using is
        port-based. You also need to pass in either a src_group_id or
        cidr_ip.

        :type group_name: string
        :param group_id:  The name of the security group you are removing
            the rule from.

        :type ip_protocol: string
        :param ip_protocol: Either tcp | udp | icmp | -1

        :type from_port: int
        :param from_port: The beginning port number you are disabling

        :type to_port: int
        :param to_port: The ending port number you are disabling

        :type src_group_id: src_group_id
        :param src_group_id: The source security group you are
            revoking access to.

        :type cidr_ip: string
        :param cidr_ip: The CIDR block you are revoking access to.
            See http://goo.gl/Yj5QC

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful.
        """

        params = {}
        if group_id:
            params['GroupId'] = group_id
        if ip_protocol:
            params['IpPermissions.1.IpProtocol'] = ip_protocol
        if from_port is not None:
            params['IpPermissions.1.FromPort'] = from_port
        if to_port is not None:
            params['IpPermissions.1.ToPort'] = to_port
        if src_group_id is not None:
            params['IpPermissions.1.Groups.1.GroupId'] = src_group_id
        if cidr_ip:
            params['IpPermissions.1.IpRanges.1.CidrIp'] = cidr_ip
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('RevokeSecurityGroupEgress',
                               params, verb='POST')

    #
    # Regions
    #

    def get_all_regions(self, region_names=None, filters=None, dry_run=False):
        """
        Get all available regions for the EC2 service.

        :type region_names: list of str
        :param region_names: Names of regions to limit output

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.regioninfo.RegionInfo`
        """
        params = {}
        if region_names:
            self.build_list_params(params, region_names, 'RegionName')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        regions = self.get_list('DescribeRegions', params,
                                [('item', RegionInfo)], verb='POST')
        for region in regions:
            region.connection_cls = EC2Connection
        return regions

    #
    # Reservation methods
    #

    def get_all_reserved_instances_offerings(self,
                                             reserved_instances_offering_ids=None,
                                             instance_type=None,
                                             availability_zone=None,
                                             product_description=None,
                                             filters=None,
                                             instance_tenancy=None,
                                             offering_type=None,
                                             include_marketplace=None,
                                             min_duration=None,
                                             max_duration=None,
                                             max_instance_count=None,
                                             next_token=None,
                                             max_results=None,
                                             dry_run=False):
        """
        Describes Reserved Instance offerings that are available for purchase.

        :type reserved_instances_offering_ids: list
        :param reserved_instances_id: One or more Reserved Instances
            offering IDs.

        :type instance_type: str
        :param instance_type: Displays Reserved Instances of the specified
                              instance type.

        :type availability_zone: str
        :param availability_zone: Displays Reserved Instances within the
                                  specified Availability Zone.

        :type product_description: str
        :param product_description: Displays Reserved Instances with the
                                    specified product description.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type instance_tenancy: string
        :param instance_tenancy: The tenancy of the Reserved Instance offering.
            A Reserved Instance with tenancy of dedicated will run on
            single-tenant hardware and can only be launched within a VPC.

        :type offering_type: string
        :param offering_type: The Reserved Instance offering type.  Valid
            Values: `"Heavy Utilization" | "Medium Utilization" | "Light
            Utilization"`

        :type include_marketplace: bool
        :param include_marketplace: Include Marketplace offerings in the
            response.

        :type min_duration: int :param min_duration: Minimum duration (in
            seconds) to filter when searching for offerings.

        :type max_duration: int
        :param max_duration: Maximum duration (in seconds) to filter when
            searching for offerings.

        :type max_instance_count: int
        :param max_instance_count: Maximum number of instances to filter when
            searching for offerings.

        :type next_token: string
        :param next_token: Token to use when requesting the next paginated set
            of offerings.

        :type max_results: int
        :param max_results: Maximum number of offerings to return per call.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of
            :class:`boto.ec2.reservedinstance.ReservedInstancesOffering`.

        """
        params = {}
        if reserved_instances_offering_ids is not None:
            self.build_list_params(params, reserved_instances_offering_ids,
                                   'ReservedInstancesOfferingId')
        if instance_type:
            params['InstanceType'] = instance_type
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if product_description:
            params['ProductDescription'] = product_description
        if filters:
            self.build_filter_params(params, filters)
        if instance_tenancy is not None:
            params['InstanceTenancy'] = instance_tenancy
        if offering_type is not None:
            params['OfferingType'] = offering_type
        if include_marketplace is not None:
            if include_marketplace:
                params['IncludeMarketplace'] = 'true'
            else:
                params['IncludeMarketplace'] = 'false'
        if min_duration is not None:
            params['MinDuration'] = str(min_duration)
        if max_duration is not None:
            params['MaxDuration'] = str(max_duration)
        if max_instance_count is not None:
            params['MaxInstanceCount'] = str(max_instance_count)
        if next_token is not None:
            params['NextToken'] = next_token
        if max_results is not None:
            params['MaxResults'] = str(max_results)
        if dry_run:
            params['DryRun'] = 'true'

        return self.get_list('DescribeReservedInstancesOfferings',
                             params, [('item', ReservedInstancesOffering)],
                             verb='POST')

    def get_all_reserved_instances(self, reserved_instances_id=None,
                                   filters=None, dry_run=False):
        """
        Describes one or more of the Reserved Instances that you purchased.

        :type reserved_instance_ids: list
        :param reserved_instance_ids: A list of the reserved instance ids that
            will be returned. If not provided, all reserved instances
            will be returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.reservedinstance.ReservedInstance`
        """
        params = {}
        if reserved_instances_id:
            self.build_list_params(params, reserved_instances_id,
                                   'ReservedInstancesId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeReservedInstances',
                             params, [('item', ReservedInstance)], verb='POST')

    def purchase_reserved_instance_offering(self,
                                            reserved_instances_offering_id,
                                            instance_count=1, limit_price=None,
                                            dry_run=False):
        """
        Purchase a Reserved Instance for use with your account.
        ** CAUTION **
        This request can result in large amounts of money being charged to your
        AWS account.  Use with caution!

        :type reserved_instances_offering_id: string
        :param reserved_instances_offering_id: The offering ID of the Reserved
            Instance to purchase

        :type instance_count: int
        :param instance_count: The number of Reserved Instances to purchase.
            Default value is 1.

        :type limit_price: tuple
        :param instance_count: Limit the price on the total order.
            Must be a tuple of (amount, currency_code), for example:
            (100.0, 'USD').

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.reservedinstance.ReservedInstance`
        :return: The newly created Reserved Instance
        """
        params = {
            'ReservedInstancesOfferingId': reserved_instances_offering_id,
            'InstanceCount': instance_count}
        if limit_price is not None:
            params['LimitPrice.Amount'] = str(limit_price[0])
            params['LimitPrice.CurrencyCode'] = str(limit_price[1])
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('PurchaseReservedInstancesOffering', params,
                               ReservedInstance, verb='POST')

    def create_reserved_instances_listing(self, reserved_instances_id,
                                          instance_count, price_schedules,
                                          client_token, dry_run=False):
        """Creates a new listing for Reserved Instances.

        Creates a new listing for Amazon EC2 Reserved Instances that will be
        sold in the Reserved Instance Marketplace. You can submit one Reserved
        Instance listing at a time.

        The Reserved Instance Marketplace matches sellers who want to resell
        Reserved Instance capacity that they no longer need with buyers who
        want to purchase additional capacity. Reserved Instances bought and
        sold through the Reserved Instance Marketplace work like any other
        Reserved Instances.

        If you want to sell your Reserved Instances, you must first register as
        a Seller in the Reserved Instance Marketplace. After completing the
        registration process, you can create a Reserved Instance Marketplace
        listing of some or all of your Reserved Instances, and specify the
        upfront price you want to receive for them. Your Reserved Instance
        listings then become available for purchase.

        :type reserved_instances_id: string
        :param reserved_instances_id: The ID of the Reserved Instance that
            will be listed.

        :type instance_count: int
        :param instance_count: The number of instances that are a part of a
            Reserved Instance account that will be listed in the Reserved
            Instance Marketplace. This number should be less than or equal to
            the instance count associated with the Reserved Instance ID
            specified in this call.

        :type price_schedules: List of tuples
        :param price_schedules: A list specifying the price of the Reserved
            Instance for each month remaining in the Reserved Instance term.
            Each tuple contains two elements, the price and the term.  For
            example, for an instance that 11 months remaining in its term,
            we can have a price schedule with an upfront price of $2.50.
            At 8 months remaining we can drop the price down to $2.00.
            This would be expressed as::

                price_schedules=[('2.50', 11), ('2.00', 8)]

        :type client_token: string
        :param client_token: Unique, case-sensitive identifier you provide
            to ensure idempotency of the request.  Maximum 64 ASCII characters.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of
            :class:`boto.ec2.reservedinstance.ReservedInstanceListing`

        """
        params = {
            'ReservedInstancesId': reserved_instances_id,
            'InstanceCount': str(instance_count),
            'ClientToken': client_token,
        }
        for i, schedule in enumerate(price_schedules):
            price, term = schedule
            params['PriceSchedules.%s.Price' % i] = str(price)
            params['PriceSchedules.%s.Term' % i] = str(term)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('CreateReservedInstancesListing',
                             params, [('item', ReservedInstanceListing)], verb='POST')

    def cancel_reserved_instances_listing(self,
                                          reserved_instances_listing_ids=None,
                                          dry_run=False):
        """Cancels the specified Reserved Instance listing.

        :type reserved_instances_listing_ids: List of strings
        :param reserved_instances_listing_ids: The ID of the
            Reserved Instance listing to be cancelled.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of
            :class:`boto.ec2.reservedinstance.ReservedInstanceListing`

        """
        params = {}
        if reserved_instances_listing_ids is not None:
            self.build_list_params(params, reserved_instances_listing_ids,
                                   'ReservedInstancesListingId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('CancelReservedInstancesListing',
                             params, [('item', ReservedInstanceListing)], verb='POST')

    def build_configurations_param_list(self, params, target_configurations):
        for offset, tc in enumerate(target_configurations):
            prefix = 'ReservedInstancesConfigurationSetItemType.%d.' % offset
            if tc.availability_zone is not None:
                params[prefix + 'AvailabilityZone'] = tc.availability_zone
            if tc.platform is not None:
                params[prefix + 'Platform'] = tc.platform
            if tc.instance_count is not None:
                params[prefix + 'InstanceCount'] = tc.instance_count
            if tc.instance_type is not None:
                params[prefix + 'InstanceType'] = tc.instance_type

    def modify_reserved_instances(self, client_token, reserved_instance_ids,
                                  target_configurations):
        """
        Modifies the specified Reserved Instances.

        :type client_token: string
        :param client_token: A unique, case-sensitive, token you provide to
                             ensure idempotency of your modification request.

        :type reserved_instance_ids: List of strings
        :param reserved_instance_ids: The IDs of the Reserved Instances to
                                      modify.

        :type target_configurations: List of :class:`boto.ec2.reservedinstance.ReservedInstancesConfiguration`
        :param target_configurations: The configuration settings for the
                                      modified Reserved Instances.

        :rtype: string
        :return: The unique ID for the submitted modification request.
        """
        params = {}
        if client_token is not None:
            params['ClientToken'] = client_token
        if reserved_instance_ids is not None:
            self.build_list_params(params, reserved_instance_ids,
                                   'ReservedInstancesId')
        if target_configurations is not None:
            self.build_configurations_param_list(params, target_configurations)
        mrir = self.get_object(
            'ModifyReservedInstances',
            params,
            ModifyReservedInstancesResult,
            verb='POST'
        )
        return mrir.modification_id

    def describe_reserved_instances_modifications(self,
            reserved_instances_modification_ids=None, next_token=None,
            filters=None):
        """
        A request to describe the modifications made to Reserved Instances in
        your account.

        :type reserved_instances_modification_ids: list
        :param reserved_instances_modification_ids: An optional list of
            Reserved Instances modification IDs to describe.

        :type next_token: str
        :param next_token: A string specifying the next paginated set
            of results to return.

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :rtype: list
        :return: A list of :class:`boto.ec2.reservedinstance.ReservedInstance`
        """
        params = {}
        if reserved_instances_modification_ids:
            self.build_list_params(params, reserved_instances_modification_ids,
                                   'ReservedInstancesModificationId')
        if next_token:
            params['NextToken'] = next_token
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeReservedInstancesModifications',
                             params, [('item', ReservedInstancesModification)],
                             verb='POST')

    #
    # Monitoring
    #

    def monitor_instances(self, instance_ids, dry_run=False):
        """
        Enable detailed CloudWatch monitoring for the supplied instances.

        :type instance_id: list of strings
        :param instance_id: The instance ids

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.instanceinfo.InstanceInfo`
        """
        params = {}
        self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('MonitorInstances', params,
                             [('item', InstanceInfo)], verb='POST')

    def monitor_instance(self, instance_id, dry_run=False):
        """
        Deprecated Version, maintained for backward compatibility.
        Enable detailed CloudWatch monitoring for the supplied instance.

        :type instance_id: string
        :param instance_id: The instance id

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.instanceinfo.InstanceInfo`
        """
        return self.monitor_instances([instance_id], dry_run=dry_run)

    def unmonitor_instances(self, instance_ids, dry_run=False):
        """
        Disable CloudWatch monitoring for the supplied instance.

        :type instance_id: list of string
        :param instance_id: The instance id

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.instanceinfo.InstanceInfo`
        """
        params = {}
        self.build_list_params(params, instance_ids, 'InstanceId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('UnmonitorInstances', params,
                             [('item', InstanceInfo)], verb='POST')

    def unmonitor_instance(self, instance_id, dry_run=False):
        """
        Deprecated Version, maintained for backward compatibility.
        Disable detailed CloudWatch monitoring for the supplied instance.

        :type instance_id: string
        :param instance_id: The instance id

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.instanceinfo.InstanceInfo`
        """
        return self.unmonitor_instances([instance_id], dry_run=dry_run)

    #
    # Bundle Windows Instances
    #

    def bundle_instance(self, instance_id,
                        s3_bucket,
                        s3_prefix,
                        s3_upload_policy, dry_run=False):
        """
        Bundle Windows instance.

        :type instance_id: string
        :param instance_id: The instance id

        :type s3_bucket: string
        :param s3_bucket: The bucket in which the AMI should be stored.

        :type s3_prefix: string
        :param s3_prefix: The beginning of the file name for the AMI.

        :type s3_upload_policy: string
        :param s3_upload_policy: Base64 encoded policy that specifies condition
                                 and permissions for Amazon EC2 to upload the
                                 user's image into Amazon S3.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """

        params = {'InstanceId': instance_id,
                  'Storage.S3.Bucket': s3_bucket,
                  'Storage.S3.Prefix': s3_prefix,
                  'Storage.S3.UploadPolicy': s3_upload_policy}
        s3auth = boto.auth.get_auth_handler(None, boto.config,
                                            self.provider, ['s3'])
        params['Storage.S3.AWSAccessKeyId'] = self.aws_access_key_id
        signature = s3auth.sign_string(s3_upload_policy)
        params['Storage.S3.UploadPolicySignature'] = signature
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('BundleInstance', params,
                               BundleInstanceTask, verb='POST')

    def get_all_bundle_tasks(self, bundle_ids=None, filters=None,
                             dry_run=False):
        """
        Retrieve current bundling tasks. If no bundle id is specified, all
        tasks are retrieved.

        :type bundle_ids: list
        :param bundle_ids: A list of strings containing identifiers for
                           previously created bundling tasks.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {}
        if bundle_ids:
            self.build_list_params(params, bundle_ids, 'BundleId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeBundleTasks', params,
                             [('item', BundleInstanceTask)], verb='POST')

    def cancel_bundle_task(self, bundle_id, dry_run=False):
        """
        Cancel a previously submitted bundle task

        :type bundle_id: string
        :param bundle_id: The identifier of the bundle task to cancel.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'BundleId': bundle_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CancelBundleTask', params,
                               BundleInstanceTask, verb='POST')

    def get_password_data(self, instance_id, dry_run=False):
        """
        Get encrypted administrator password for a Windows instance.

        :type instance_id: string
        :param instance_id: The identifier of the instance to retrieve the
                            password for.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'InstanceId': instance_id}
        if dry_run:
            params['DryRun'] = 'true'
        rs = self.get_object('GetPasswordData', params, ResultSet, verb='POST')
        return rs.passwordData

    #
    # Cluster Placement Groups
    #

    def get_all_placement_groups(self, groupnames=None, filters=None,
                                 dry_run=False):
        """
        Get all placement groups associated with your account in a region.

        :type groupnames: list
        :param groupnames: A list of the names of placement groups to retrieve.
                           If not provided, all placement groups will be
                           returned.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.placementgroup.PlacementGroup`
        """
        params = {}
        if groupnames:
            self.build_list_params(params, groupnames, 'GroupName')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribePlacementGroups', params,
                             [('item', PlacementGroup)], verb='POST')

    def create_placement_group(self, name, strategy='cluster', dry_run=False):
        """
        Create a new placement group for your account.
        This will create the placement group within the region you
        are currently connected to.

        :type name: string
        :param name: The name of the new placement group

        :type strategy: string
        :param strategy: The placement strategy of the new placement group.
                         Currently, the only acceptable value is "cluster".

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: bool
        :return: True if successful
        """
        params = {'GroupName': name, 'Strategy': strategy}
        if dry_run:
            params['DryRun'] = 'true'
        group = self.get_status('CreatePlacementGroup', params, verb='POST')
        return group

    def delete_placement_group(self, name, dry_run=False):
        """
        Delete a placement group from your account.

        :type key_name: string
        :param key_name: The name of the keypair to delete

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'GroupName': name}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeletePlacementGroup', params, verb='POST')

    # Tag methods

    def build_tag_param_list(self, params, tags):
        keys = sorted(tags.keys())
        i = 1
        for key in keys:
            value = tags[key]
            params['Tag.%d.Key' % i] = key
            if value is not None:
                params['Tag.%d.Value' % i] = value
            i += 1

    def get_all_tags(self, filters=None, dry_run=False, max_results=None):
        """
        Retrieve all the metadata tags associated with your account.

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :rtype: list
        :return: A list of :class:`boto.ec2.tag.Tag` objects
        """
        params = {}
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        if max_results is not None:
            params['MaxResults'] = max_results
        return self.get_list('DescribeTags', params,
                             [('item', Tag)], verb='POST')

    def create_tags(self, resource_ids, tags, dry_run=False):
        """
        Create new metadata tags for the specified resource ids.

        :type resource_ids: list
        :param resource_ids: List of strings

        :type tags: dict
        :param tags: A dictionary containing the name/value pairs.
                     If you want to create only a tag name, the
                     value for that tag should be the empty string
                     (e.g. '').

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {}
        self.build_list_params(params, resource_ids, 'ResourceId')
        self.build_tag_param_list(params, tags)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('CreateTags', params, verb='POST')

    def delete_tags(self, resource_ids, tags, dry_run=False):
        """
        Delete metadata tags for the specified resource ids.

        :type resource_ids: list
        :param resource_ids: List of strings

        :type tags: dict or list
        :param tags: Either a dictionary containing name/value pairs
                     or a list containing just tag names.
                     If you pass in a dictionary, the values must
                     match the actual tag values or the tag will
                     not be deleted.  If you pass in a value of None
                     for the tag value, all tags with that name will
                     be deleted.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        if isinstance(tags, list):
            tags = {}.fromkeys(tags, None)
        params = {}
        self.build_list_params(params, resource_ids, 'ResourceId')
        self.build_tag_param_list(params, tags)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteTags', params, verb='POST')

    # Network Interface methods

    def get_all_network_interfaces(self, network_interface_ids=None, filters=None, dry_run=False):
        """
        Retrieve all of the Elastic Network Interfaces (ENI's)
        associated with your account.

        :type network_interface_ids: list
        :param network_interface_ids: a list of strings representing ENI IDs

        :type filters: dict
        :param filters: Optional filters that can be used to limit
                        the results returned.  Filters are provided
                        in the form of a dictionary consisting of
                        filter names as the key and filter values
                        as the value.  The set of allowable filter
                        names/values is dependent on the request
                        being performed.  Check the EC2 API guide
                        for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: list
        :return: A list of :class:`boto.ec2.networkinterface.NetworkInterface`
        """
        params = {}
        if network_interface_ids:
            self.build_list_params(params, network_interface_ids, 'NetworkInterfaceId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeNetworkInterfaces', params,
                             [('item', NetworkInterface)], verb='POST')

    def create_network_interface(self, subnet_id, private_ip_address=None,
                                 description=None, groups=None, dry_run=False):
        """
        Creates a network interface in the specified subnet.

        :type subnet_id: str
        :param subnet_id: The ID of the subnet to associate with the
            network interface.

        :type private_ip_address: str
        :param private_ip_address: The private IP address of the
            network interface.  If not supplied, one will be chosen
            for you.

        :type description: str
        :param description: The description of the network interface.

        :type groups: list
        :param groups: Lists the groups for use by the network interface.
            This can be either a list of group ID's or a list of
            :class:`boto.ec2.securitygroup.SecurityGroup` objects.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :rtype: :class:`boto.ec2.networkinterface.NetworkInterface`
        :return: The newly created network interface.
        """
        params = {'SubnetId': subnet_id}
        if private_ip_address:
            params['PrivateIpAddress'] = private_ip_address
        if description:
            params['Description'] = description
        if groups:
            ids = []
            for group in groups:
                if isinstance(group, SecurityGroup):
                    ids.append(group.id)
                else:
                    ids.append(group)
            self.build_list_params(params, ids, 'SecurityGroupId')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateNetworkInterface', params,
                               NetworkInterface, verb='POST')

    def attach_network_interface(self, network_interface_id,
                                 instance_id, device_index, dry_run=False):
        """
        Attaches a network interface to an instance.

        :type network_interface_id: str
        :param network_interface_id: The ID of the network interface to attach.

        :type instance_id: str
        :param instance_id: The ID of the instance that will be attached
            to the network interface.

        :type device_index: int
        :param device_index: The index of the device for the network
            interface attachment on the instance.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'NetworkInterfaceId': network_interface_id,
                  'InstanceId': instance_id,
                  'DeviceIndex': device_index}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('AttachNetworkInterface', params, verb='POST')

    def detach_network_interface(self, attachment_id, force=False,
                                 dry_run=False):
        """
        Detaches a network interface from an instance.

        :type attachment_id: str
        :param attachment_id: The ID of the attachment.

        :type force: bool
        :param force: Set to true to force a detachment.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'AttachmentId': attachment_id}
        if force:
            params['Force'] = 'true'
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DetachNetworkInterface', params, verb='POST')

    def delete_network_interface(self, network_interface_id, dry_run=False):
        """
        Delete the specified network interface.

        :type network_interface_id: str
        :param network_interface_id: The ID of the network interface to delete.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {'NetworkInterfaceId': network_interface_id}
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('DeleteNetworkInterface', params, verb='POST')

    def get_all_instance_types(self):
        """
        Get all instance_types available on this cloud (eucalyptus specific)

        :rtype: list of :class:`boto.ec2.instancetype.InstanceType`
        :return: The requested InstanceType objects
        """
        params = {}
        return self.get_list('DescribeInstanceTypes', params, [('item', InstanceType)], verb='POST')

    def copy_image(self, source_region, source_image_id, name=None,
                   description=None, client_token=None, dry_run=False,
                   encrypted=None, kms_key_id=None):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.
        :rtype: :class:`boto.ec2.image.CopyImage`
        :return: Object containing the image_id of the copied image.
        """
        params = {
            'SourceRegion': source_region,
            'SourceImageId': source_image_id,
        }
        if name is not None:
            params['Name'] = name
        if description is not None:
            params['Description'] = description
        if client_token is not None:
            params['ClientToken'] = client_token
        if encrypted is not None:
            params['Encrypted'] = 'true' if encrypted else 'false'
        if kms_key_id is not None:
            params['KmsKeyId'] = kms_key_id
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CopyImage', params, CopyImage,
                               verb='POST')

    def describe_account_attributes(self, attribute_names=None, dry_run=False):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {}
        if attribute_names is not None:
            self.build_list_params(params, attribute_names, 'AttributeName')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeAccountAttributes', params,
                             [('item', AccountAttribute)], verb='POST')

    def describe_vpc_attribute(self, vpc_id, attribute=None, dry_run=False):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {
            'VpcId': vpc_id
        }
        if attribute is not None:
            params['Attribute'] = attribute
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('DescribeVpcAttribute', params,
                               VPCAttribute, verb='POST')

    def modify_vpc_attribute(self, vpc_id, enable_dns_support=None,
                             enable_dns_hostnames=None, dry_run=False):
        """
        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        """
        params = {
            'VpcId': vpc_id
        }
        if enable_dns_support is not None:
            params['EnableDnsSupport.Value'] = (
                'true' if enable_dns_support else 'false')
        if enable_dns_hostnames is not None:
            params['EnableDnsHostnames.Value'] = (
                'true' if enable_dns_hostnames else 'false')
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_status('ModifyVpcAttribute', params, verb='POST')

    def get_all_classic_link_instances(self, instance_ids=None, filters=None,
                                       dry_run=False, max_results=None,
                                       next_token=None):
        """
        Get all of your linked EC2-Classic instances. This request only
        returns information about EC2-Classic instances linked  to
        a VPC through ClassicLink

        :type instance_ids: list
        :param instance_ids: A list of strings of instance IDs. Must be
            instances linked to a VPC through ClassicLink.

        :type filters: dict
        :param filters: Optional filters that can be used to limit the
            results returned.  Filters are provided in the form of a
            dictionary consisting of filter names as the key and
            filter values as the value.  The set of allowable filter
            names/values is dependent on the request being performed.
            Check the EC2 API guide for details.

        :type dry_run: bool
        :param dry_run: Set to True if the operation should not actually run.

        :type max_results: int
        :param max_results: The maximum number of paginated instance
            items per response.

        :rtype: list
        :return: A list of  :class:`boto.ec2.instance.Instance`
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceId')
        if filters:
            self.build_filter_params(params, filters)
        if dry_run:
            params['DryRun'] = 'true'
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeClassicLinkInstances', params,
                             [('item', Instance)], verb='POST')
