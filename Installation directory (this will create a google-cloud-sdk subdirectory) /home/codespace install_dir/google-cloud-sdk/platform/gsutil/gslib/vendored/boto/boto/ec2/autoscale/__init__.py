# Copyright (c) 2009-2011 Reza Lotun http://reza.lotun.name/
# Copyright (c) 2011 Jann Kleen
# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
This module provides an interface to the Elastic Compute Cloud (EC2)
Auto Scaling service.
"""

import base64

import boto
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo, get_regions, load_regions
from boto.regioninfo import connect
from boto.ec2.autoscale.request import Request
from boto.ec2.autoscale.launchconfig import LaunchConfiguration
from boto.ec2.autoscale.group import AutoScalingGroup
from boto.ec2.autoscale.group import ProcessType
from boto.ec2.autoscale.activity import Activity
from boto.ec2.autoscale.policy import AdjustmentType
from boto.ec2.autoscale.policy import MetricCollectionTypes
from boto.ec2.autoscale.policy import ScalingPolicy
from boto.ec2.autoscale.policy import TerminationPolicies
from boto.ec2.autoscale.instance import Instance
from boto.ec2.autoscale.scheduled import ScheduledUpdateGroupAction
from boto.ec2.autoscale.tag import Tag
from boto.ec2.autoscale.limits import AccountLimits
from boto.compat import six

RegionData = load_regions().get('autoscaling', {})


def regions():
    """
    Get all available regions for the Auto Scaling service.

    :rtype: list
    :return: A list of :class:`boto.RegionInfo` instances
    """
    return get_regions('autoscaling', connection_cls=AutoScaleConnection)


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.ec2.autoscale.AutoScaleConnection`.

    :param str region_name: The name of the region to connect to.

    :rtype: :class:`boto.ec2.AutoScaleConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
        name is given
    """
    return connect('autoscaling', region_name,
                   connection_cls=AutoScaleConnection, **kw_params)


class AutoScaleConnection(AWSQueryConnection):
    APIVersion = boto.config.get('Boto', 'autoscale_version', '2011-01-01')
    DefaultRegionEndpoint = boto.config.get('Boto', 'autoscale_endpoint',
                                            'autoscaling.us-east-1.amazonaws.com')
    DefaultRegionName = boto.config.get('Boto', 'autoscale_region_name',
                                        'us-east-1')

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True, profile_name=None,
                 use_block_device_types=False):
        """
        Init method to create a new connection to the AutoScaling service.

        B{Note:} The host argument is overridden by the host specified in the
                 boto configuration file.


        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint,
                                AutoScaleConnection)
        self.region = region
        self.use_block_device_types = use_block_device_types
        super(AutoScaleConnection, self).__init__(aws_access_key_id,
                                                  aws_secret_access_key,
                                                  is_secure, port, proxy, proxy_port,
                                                  proxy_user, proxy_pass,
                                                  self.region.endpoint, debug,
                                                  https_connection_factory, path=path,
                                                  security_token=security_token,
                                                  validate_certs=validate_certs,
                                                  profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def build_list_params(self, params, items, label):
        """
        Items is a list of dictionaries or strings::

            [
                {
                    'Protocol' : 'HTTP',
                    'LoadBalancerPort' : '80',
                    'InstancePort' : '80'
                },
                ..
            ] etc.

        or::

            ['us-east-1b',...]
        """
        # different from EC2 list params
        for i in range(1, len(items) + 1):
            if isinstance(items[i - 1], dict):
                for k, v in six.iteritems(items[i - 1]):
                    if isinstance(v, dict):
                        for kk, vv in six.iteritems(v):
                            params['%s.member.%d.%s.%s' % (label, i, k, kk)] = vv
                    else:
                        params['%s.member.%d.%s' % (label, i, k)] = v
            elif isinstance(items[i - 1], six.string_types):
                params['%s.member.%d' % (label, i)] = items[i - 1]

    def _update_group(self, op, as_group):
        params = {'AutoScalingGroupName': as_group.name,
                  'LaunchConfigurationName': as_group.launch_config_name,
                  'MinSize': as_group.min_size,
                  'MaxSize': as_group.max_size}
        # get availability zone information (required param)
        zones = as_group.availability_zones
        self.build_list_params(params, zones, 'AvailabilityZones')
        if as_group.desired_capacity is not None:
            params['DesiredCapacity'] = as_group.desired_capacity
        if as_group.vpc_zone_identifier:
            params['VPCZoneIdentifier'] = as_group.vpc_zone_identifier
        if as_group.health_check_period:
            params['HealthCheckGracePeriod'] = as_group.health_check_period
        if as_group.health_check_type:
            params['HealthCheckType'] = as_group.health_check_type
        if as_group.default_cooldown:
            params['DefaultCooldown'] = as_group.default_cooldown
        if as_group.placement_group:
            params['PlacementGroup'] = as_group.placement_group
        if as_group.instance_id:
            params['InstanceId'] = as_group.instance_id
        if as_group.termination_policies:
            self.build_list_params(params, as_group.termination_policies,
                                   'TerminationPolicies')
        if op.startswith('Create'):
            # you can only associate load balancers with an autoscale
            # group at creation time
            if as_group.load_balancers:
                self.build_list_params(params, as_group.load_balancers,
                                       'LoadBalancerNames')
            if as_group.tags:
                for i, tag in enumerate(as_group.tags):
                    tag.build_params(params, i + 1)
        return self.get_object(op, params, Request)

    def attach_instances(self, name, instance_ids):
        """
        Attach instances to an autoscaling group.
        """
        params = {
            'AutoScalingGroupName': name,
        }
        self.build_list_params(params, instance_ids, 'InstanceIds')
        return self.get_status('AttachInstances', params)

    def detach_instances(self, name, instance_ids, decrement_capacity=True):
        """
        Detach instances from an Auto Scaling group.

        :type name: str
        :param name: The name of the Auto Scaling group from which to detach instances.

        :type instance_ids: list
        :param instance_ids: Instance ids to be detached from the Auto Scaling group.

        :type decrement_capacity: bool
        :param decrement_capacity: Whether to decrement the size of the
            Auto Scaling group or not.
        """

        params = {'AutoScalingGroupName': name}
        params['ShouldDecrementDesiredCapacity'] = 'true' if decrement_capacity else 'false'

        self.build_list_params(params, instance_ids, 'InstanceIds')
        return self.get_status('DetachInstances', params)

    def create_auto_scaling_group(self, as_group):
        """
        Create auto scaling group.
        """
        return self._update_group('CreateAutoScalingGroup', as_group)

    def delete_auto_scaling_group(self, name, force_delete=False):
        """
        Deletes the specified auto scaling group if the group has no instances
        and no scaling activities in progress.
        """
        if(force_delete):
            params = {'AutoScalingGroupName': name, 'ForceDelete': 'true'}
        else:
            params = {'AutoScalingGroupName': name}
        return self.get_object('DeleteAutoScalingGroup', params, Request)

    def create_launch_configuration(self, launch_config):
        """
        Creates a new Launch Configuration.

        :type launch_config: :class:`boto.ec2.autoscale.launchconfig.LaunchConfiguration`
        :param launch_config: LaunchConfiguration object.
        """
        params = {'ImageId': launch_config.image_id,
                  'LaunchConfigurationName': launch_config.name,
                  'InstanceType': launch_config.instance_type}
        if launch_config.key_name:
            params['KeyName'] = launch_config.key_name
        if launch_config.user_data:
            user_data = launch_config.user_data
            if isinstance(user_data, six.text_type):
                user_data = user_data.encode('utf-8')
            params['UserData'] = base64.b64encode(user_data).decode('utf-8')
        if launch_config.kernel_id:
            params['KernelId'] = launch_config.kernel_id
        if launch_config.ramdisk_id:
            params['RamdiskId'] = launch_config.ramdisk_id
        if launch_config.block_device_mappings:
            [x.autoscale_build_list_params(params) for x in launch_config.block_device_mappings]
        if launch_config.security_groups:
            self.build_list_params(params, launch_config.security_groups,
                                   'SecurityGroups')
        if launch_config.instance_monitoring:
            params['InstanceMonitoring.Enabled'] = 'true'
        else:
            params['InstanceMonitoring.Enabled'] = 'false'
        if launch_config.spot_price is not None:
            params['SpotPrice'] = str(launch_config.spot_price)
        if launch_config.instance_profile_name is not None:
            params['IamInstanceProfile'] = launch_config.instance_profile_name
        if launch_config.ebs_optimized:
            params['EbsOptimized'] = 'true'
        else:
            params['EbsOptimized'] = 'false'
        if launch_config.associate_public_ip_address is True:
            params['AssociatePublicIpAddress'] = 'true'
        elif launch_config.associate_public_ip_address is False:
            params['AssociatePublicIpAddress'] = 'false'
        if launch_config.volume_type:
            params['VolumeType'] = launch_config.volume_type
        if launch_config.delete_on_termination:
            params['DeleteOnTermination'] = 'true'
        else:
            params['DeleteOnTermination'] = 'false'
        if launch_config.iops:
            params['Iops'] = launch_config.iops
        if launch_config.classic_link_vpc_id:
            params['ClassicLinkVPCId'] = launch_config.classic_link_vpc_id
        if launch_config.classic_link_vpc_security_groups:
            self.build_list_params(
                params,
                launch_config.classic_link_vpc_security_groups,
                'ClassicLinkVPCSecurityGroups'
            )
        return self.get_object('CreateLaunchConfiguration', params,
                               Request, verb='POST')

    def get_account_limits(self):
        """
        Returns the limits for the Auto Scaling resources currently granted for
        your AWS account.
        """
        params = {}
        return self.get_object('DescribeAccountLimits', params, AccountLimits)

    def create_scaling_policy(self, scaling_policy):
        """
        Creates a new Scaling Policy.

        :type scaling_policy: :class:`boto.ec2.autoscale.policy.ScalingPolicy`
        :param scaling_policy: ScalingPolicy object.
        """
        params = {'AdjustmentType': scaling_policy.adjustment_type,
                  'AutoScalingGroupName': scaling_policy.as_name,
                  'PolicyName': scaling_policy.name,
                  'ScalingAdjustment': scaling_policy.scaling_adjustment}

        if scaling_policy.adjustment_type == "PercentChangeInCapacity" and \
           scaling_policy.min_adjustment_step is not None:
            params['MinAdjustmentStep'] = scaling_policy.min_adjustment_step

        if scaling_policy.cooldown is not None:
            params['Cooldown'] = scaling_policy.cooldown

        return self.get_object('PutScalingPolicy', params, Request)

    def delete_launch_configuration(self, launch_config_name):
        """
        Deletes the specified LaunchConfiguration.

        The specified launch configuration must not be attached to an Auto
        Scaling group. Once this call completes, the launch configuration is no
        longer available for use.
        """
        params = {'LaunchConfigurationName': launch_config_name}
        return self.get_object('DeleteLaunchConfiguration', params, Request)

    def get_all_groups(self, names=None, max_records=None, next_token=None):
        """
        Returns a full description of each Auto Scaling group in the given
        list. This includes all Amazon EC2 instances that are members of the
        group. If a list of names is not provided, the service returns the full
        details of all Auto Scaling groups.

        This action supports pagination by returning a token if there are more
        pages to retrieve. To get the next page, call this action again with
        the returned token as the NextToken parameter.

        :type names: list
        :param names: List of group names which should be searched for.

        :type max_records: int
        :param max_records: Maximum amount of groups to return.

        :rtype: list
        :returns: List of :class:`boto.ec2.autoscale.group.AutoScalingGroup`
            instances.
        """
        params = {}
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        if names:
            self.build_list_params(params, names, 'AutoScalingGroupNames')
        return self.get_list('DescribeAutoScalingGroups', params,
                             [('member', AutoScalingGroup)])

    def get_all_launch_configurations(self, **kwargs):
        """
        Returns a full description of the launch configurations given the
        specified names.

        If no names are specified, then the full details of all launch
        configurations are returned.

        :type names: list
        :param names: List of configuration names which should be searched for.

        :type max_records: int
        :param max_records: Maximum amount of configurations to return.

        :type next_token: str
        :param next_token: If you have more results than can be returned
            at once, pass in this  parameter to page through all results.

        :rtype: list
        :returns: List of
            :class:`boto.ec2.autoscale.launchconfig.LaunchConfiguration`
            instances.
        """
        params = {}
        max_records = kwargs.get('max_records', None)
        names = kwargs.get('names', None)
        if max_records is not None:
            params['MaxRecords'] = max_records
        if names:
            self.build_list_params(params, names, 'LaunchConfigurationNames')
        next_token = kwargs.get('next_token')
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeLaunchConfigurations', params,
                             [('member', LaunchConfiguration)])

    def get_all_activities(self, autoscale_group, activity_ids=None,
                           max_records=None, next_token=None):
        """
        Get all activities for the given autoscaling group.

        This action supports pagination by returning a token if there are more
        pages to retrieve. To get the next page, call this action again with
        the returned token as the NextToken parameter

        :type autoscale_group: str or
            :class:`boto.ec2.autoscale.group.AutoScalingGroup` object
        :param autoscale_group: The auto scaling group to get activities on.

        :type max_records: int
        :param max_records: Maximum amount of activities to return.

        :rtype: list
        :returns: List of
            :class:`boto.ec2.autoscale.activity.Activity` instances.
        """
        name = autoscale_group
        if isinstance(autoscale_group, AutoScalingGroup):
            name = autoscale_group.name
        params = {'AutoScalingGroupName': name}
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        if activity_ids:
            self.build_list_params(params, activity_ids, 'ActivityIds')
        return self.get_list('DescribeScalingActivities',
                             params, [('member', Activity)])

    def get_termination_policies(self):
        """Gets all valid termination policies.

        These values can then be used as the termination_policies arg
        when creating and updating autoscale groups.
        """
        return self.get_object('DescribeTerminationPolicyTypes',
                               {}, TerminationPolicies)

    def delete_scheduled_action(self, scheduled_action_name,
                                autoscale_group=None):
        """
        Deletes a previously scheduled action.

        :type scheduled_action_name: str
        :param scheduled_action_name: The name of the action you want
            to delete.

        :type autoscale_group: str
        :param autoscale_group: The name of the autoscale group.
        """
        params = {'ScheduledActionName': scheduled_action_name}
        if autoscale_group:
            params['AutoScalingGroupName'] = autoscale_group
        return self.get_status('DeleteScheduledAction', params)

    def terminate_instance(self, instance_id, decrement_capacity=True):
        """
        Terminates the specified instance. The desired group size can
        also be adjusted, if desired.

        :type instance_id: str
        :param instance_id: The ID of the instance to be terminated.

        :type decrement_capability: bool
        :param decrement_capacity: Whether to decrement the size of the
            autoscaling group or not.
        """
        params = {'InstanceId': instance_id}
        if decrement_capacity:
            params['ShouldDecrementDesiredCapacity'] = 'true'
        else:
            params['ShouldDecrementDesiredCapacity'] = 'false'
        return self.get_object('TerminateInstanceInAutoScalingGroup', params,
                               Activity)

    def delete_policy(self, policy_name, autoscale_group=None):
        """
        Delete a policy.

        :type policy_name: str
        :param policy_name: The name or ARN of the policy to delete.

        :type autoscale_group: str
        :param autoscale_group: The name of the autoscale group.
        """
        params = {'PolicyName': policy_name}
        if autoscale_group:
            params['AutoScalingGroupName'] = autoscale_group
        return self.get_status('DeletePolicy', params)

    def get_all_adjustment_types(self):
        return self.get_list('DescribeAdjustmentTypes', {},
                             [('member', AdjustmentType)])

    def get_all_autoscaling_instances(self, instance_ids=None,
                                      max_records=None, next_token=None):
        """
        Returns a description of each Auto Scaling instance in the instance_ids
        list. If a list is not provided, the service returns the full details
        of all instances up to a maximum of fifty.

        This action supports pagination by returning a token if there are more
        pages to retrieve. To get the next page, call this action again with
        the returned token as the NextToken parameter.

        :type instance_ids: list
        :param instance_ids: List of Autoscaling Instance IDs which should be
            searched for.

        :type max_records: int
        :param max_records: Maximum number of results to return.

        :rtype: list
        :returns: List of
            :class:`boto.ec2.autoscale.instance.Instance` objects.
        """
        params = {}
        if instance_ids:
            self.build_list_params(params, instance_ids, 'InstanceIds')
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeAutoScalingInstances',
                             params, [('member', Instance)])

    def get_all_metric_collection_types(self):
        """
        Returns a list of metrics and a corresponding list of granularities
        for each metric.
        """
        return self.get_object('DescribeMetricCollectionTypes',
                               {}, MetricCollectionTypes)

    def get_all_policies(self, as_group=None, policy_names=None,
                         max_records=None, next_token=None):
        """
        Returns descriptions of what each policy does. This action supports
        pagination. If the response includes a token, there are more records
        available. To get the additional records, repeat the request with the
        response token as the NextToken parameter.

        If no group name or list of policy names are provided, all
        available policies are returned.

        :type as_group: str
        :param as_group: The name of the
            :class:`boto.ec2.autoscale.group.AutoScalingGroup` to filter for.

        :type policy_names: list
        :param policy_names: List of policy names which should be searched for.

        :type max_records: int
        :param max_records: Maximum amount of groups to return.

        :type next_token: str
        :param next_token: If you have more results than can be returned
            at once, pass in this  parameter to page through all results.
        """
        params = {}
        if as_group:
            params['AutoScalingGroupName'] = as_group
        if policy_names:
            self.build_list_params(params, policy_names, 'PolicyNames')
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribePolicies', params,
                             [('member', ScalingPolicy)])

    def get_all_scaling_process_types(self):
        """
        Returns scaling process types for use in the ResumeProcesses and
        SuspendProcesses actions.
        """
        return self.get_list('DescribeScalingProcessTypes', {},
                             [('member', ProcessType)])

    def suspend_processes(self, as_group, scaling_processes=None):
        """
        Suspends Auto Scaling processes for an Auto Scaling group.

        :type as_group: string
        :param as_group: The auto scaling group to suspend processes on.

        :type scaling_processes: list
        :param scaling_processes: Processes you want to suspend. If omitted,
            all processes will be suspended.
        """
        params = {'AutoScalingGroupName': as_group}
        if scaling_processes:
            self.build_list_params(params, scaling_processes,
                                   'ScalingProcesses')
        return self.get_status('SuspendProcesses', params)

    def resume_processes(self, as_group, scaling_processes=None):
        """
        Resumes Auto Scaling processes for an Auto Scaling group.

        :type as_group: string
        :param as_group: The auto scaling group to resume processes on.

        :type scaling_processes: list
        :param scaling_processes: Processes you want to resume. If omitted, all
            processes will be resumed.
        """
        params = {'AutoScalingGroupName': as_group}

        if scaling_processes:
            self.build_list_params(params, scaling_processes,
                                   'ScalingProcesses')
        return self.get_status('ResumeProcesses', params)

    def create_scheduled_group_action(self, as_group, name, time=None,
                                      desired_capacity=None,
                                      min_size=None, max_size=None,
                                      start_time=None, end_time=None,
                                      recurrence=None):
        """
        Creates a scheduled scaling action for a Auto Scaling group. If you
        leave a parameter unspecified, the corresponding value remains
        unchanged in the affected Auto Scaling group.

        :type as_group: string
        :param as_group: The auto scaling group to get activities on.

        :type name: string
        :param name: Scheduled action name.

        :type time: datetime.datetime
        :param time: The time for this action to start. (Depracated)

        :type desired_capacity: int
        :param desired_capacity: The number of EC2 instances that should
            be running in this group.

        :type min_size: int
        :param min_size: The minimum size for the new auto scaling group.

        :type max_size: int
        :param max_size: The minimum size for the new auto scaling group.

        :type start_time: datetime.datetime
        :param start_time: The time for this action to start. When StartTime and EndTime are specified with Recurrence, they form the boundaries of when the recurring action will start and stop.

        :type end_time: datetime.datetime
        :param end_time: The time for this action to end. When StartTime and EndTime are specified with Recurrence, they form the boundaries of when the recurring action will start and stop.

        :type recurrence: string
        :param recurrence: The time when recurring future actions will start. Start time is specified by the user following the Unix cron syntax format. EXAMPLE: '0 10 * * *'
        """
        params = {'AutoScalingGroupName': as_group,
                  'ScheduledActionName': name}
        if start_time is not None:
            params['StartTime'] = start_time.isoformat()
        if end_time is not None:
            params['EndTime'] = end_time.isoformat()
        if recurrence is not None:
            params['Recurrence'] = recurrence
        if time:
            params['Time'] = time.isoformat()
        if desired_capacity is not None:
            params['DesiredCapacity'] = desired_capacity
        if min_size is not None:
            params['MinSize'] = min_size
        if max_size is not None:
            params['MaxSize'] = max_size
        return self.get_status('PutScheduledUpdateGroupAction', params)

    def get_all_scheduled_actions(self, as_group=None, start_time=None,
                                  end_time=None, scheduled_actions=None,
                                  max_records=None, next_token=None):
        params = {}
        if as_group:
            params['AutoScalingGroupName'] = as_group
        if scheduled_actions:
            self.build_list_params(params, scheduled_actions,
                                   'ScheduledActionNames')
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeScheduledActions', params,
                             [('member', ScheduledUpdateGroupAction)])

    def disable_metrics_collection(self, as_group, metrics=None):
        """
        Disables monitoring of group metrics for the Auto Scaling group
        specified in AutoScalingGroupName. You can specify the list of affected
        metrics with the Metrics parameter.
        """
        params = {'AutoScalingGroupName': as_group}

        if metrics:
            self.build_list_params(params, metrics, 'Metrics')
        return self.get_status('DisableMetricsCollection', params)

    def enable_metrics_collection(self, as_group, granularity, metrics=None):
        """
        Enables monitoring of group metrics for the Auto Scaling group
        specified in AutoScalingGroupName. You can specify the list of enabled
        metrics with the Metrics parameter.

        Auto scaling metrics collection can be turned on only if the
        InstanceMonitoring.Enabled flag, in the Auto Scaling group's launch
        configuration, is set to true.

        :type autoscale_group: string
        :param autoscale_group: The auto scaling group to get activities on.

        :type granularity: string
        :param granularity: The granularity to associate with the metrics to
            collect. Currently, the only legal granularity is "1Minute".

        :type metrics: string list
        :param metrics: The list of metrics to collect. If no metrics are
                        specified, all metrics are enabled.
        """
        params = {'AutoScalingGroupName': as_group,
                  'Granularity': granularity}
        if metrics:
            self.build_list_params(params, metrics, 'Metrics')
        return self.get_status('EnableMetricsCollection', params)

    def execute_policy(self, policy_name, as_group=None, honor_cooldown=None):
        params = {'PolicyName': policy_name}
        if as_group:
            params['AutoScalingGroupName'] = as_group
        if honor_cooldown:
            params['HonorCooldown'] = honor_cooldown
        return self.get_status('ExecutePolicy', params)

    def put_notification_configuration(self, autoscale_group, topic, notification_types):
        """
        Configures an Auto Scaling group to send notifications when
        specified events take place.

        :type autoscale_group: str or
            :class:`boto.ec2.autoscale.group.AutoScalingGroup` object
        :param autoscale_group: The Auto Scaling group to put notification
            configuration on.

        :type topic: str
        :param topic: The Amazon Resource Name (ARN) of the Amazon Simple
            Notification Service (SNS) topic.

        :type notification_types: list
        :param notification_types: The type of events that will trigger
            the notification. Valid types are:
            'autoscaling:EC2_INSTANCE_LAUNCH',
            'autoscaling:EC2_INSTANCE_LAUNCH_ERROR',
            'autoscaling:EC2_INSTANCE_TERMINATE',
            'autoscaling:EC2_INSTANCE_TERMINATE_ERROR',
            'autoscaling:TEST_NOTIFICATION'
        """

        name = autoscale_group
        if isinstance(autoscale_group, AutoScalingGroup):
            name = autoscale_group.name

        params = {'AutoScalingGroupName': name,
                  'TopicARN': topic}
        self.build_list_params(params, notification_types, 'NotificationTypes')
        return self.get_status('PutNotificationConfiguration', params)

    def delete_notification_configuration(self, autoscale_group, topic):
        """
        Deletes notifications created by put_notification_configuration.

        :type autoscale_group: str or
            :class:`boto.ec2.autoscale.group.AutoScalingGroup` object
        :param autoscale_group: The Auto Scaling group to put notification
            configuration on.

        :type topic: str
        :param topic: The Amazon Resource Name (ARN) of the Amazon Simple
            Notification Service (SNS) topic.
        """

        name = autoscale_group
        if isinstance(autoscale_group, AutoScalingGroup):
            name = autoscale_group.name

        params = {'AutoScalingGroupName': name,
                  'TopicARN': topic}

        return self.get_status('DeleteNotificationConfiguration', params)

    def set_instance_health(self, instance_id, health_status,
                            should_respect_grace_period=True):
        """
        Explicitly set the health status of an instance.

        :type instance_id: str
        :param instance_id: The identifier of the EC2 instance.

        :type health_status: str
        :param health_status: The health status of the instance.
            "Healthy" means that the instance is healthy and should remain
            in service. "Unhealthy" means that the instance is unhealthy.
            Auto Scaling should terminate and replace it.

        :type should_respect_grace_period: bool
        :param should_respect_grace_period: If True, this call should
            respect the grace period associated with the group.
        """
        params = {'InstanceId': instance_id,
                  'HealthStatus': health_status}
        if should_respect_grace_period:
            params['ShouldRespectGracePeriod'] = 'true'
        else:
            params['ShouldRespectGracePeriod'] = 'false'
        return self.get_status('SetInstanceHealth', params)

    def set_desired_capacity(self, group_name, desired_capacity, honor_cooldown=False):
        """
        Adjusts the desired size of the AutoScalingGroup by initiating scaling
        activities. When reducing the size of the group, it is not possible to define
        which Amazon EC2 instances will be terminated. This applies to any Auto Scaling
        decisions that might result in terminating instances.

        :type group_name: string
        :param group_name: name of the auto scaling group

        :type desired_capacity: integer
        :param desired_capacity: new capacity setting for auto scaling group

        :type honor_cooldown: boolean
        :param honor_cooldown: by default, overrides any cooldown period
        """
        params = {'AutoScalingGroupName': group_name,
                  'DesiredCapacity': desired_capacity}
        if honor_cooldown:
            params['HonorCooldown'] = 'true'

        return self.get_status('SetDesiredCapacity', params)

    # Tag methods

    def get_all_tags(self, filters=None, max_records=None, next_token=None):
        """
        Lists the Auto Scaling group tags.

        This action supports pagination by returning a token if there
        are more pages to retrieve. To get the next page, call this
        action again with the returned token as the NextToken
        parameter.

        :type filters: dict
        :param filters: The value of the filter type used to identify
            the tags to be returned.  NOT IMPLEMENTED YET.

        :type max_records: int
        :param max_records: Maximum number of tags to return.

        :rtype: list
        :returns: List of :class:`boto.ec2.autoscale.tag.Tag`
            instances.
        """
        params = {}
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeTags', params,
                             [('member', Tag)])

    def create_or_update_tags(self, tags):
        """
        Creates new tags or updates existing tags for an Auto Scaling group.

        :type tags: List of :class:`boto.ec2.autoscale.tag.Tag`
        :param tags: The new or updated tags.
        """
        params = {}
        for i, tag in enumerate(tags):
            tag.build_params(params, i + 1)
        return self.get_status('CreateOrUpdateTags', params, verb='POST')

    def delete_tags(self, tags):
        """
        Deletes existing tags for an Auto Scaling group.

        :type tags: List of :class:`boto.ec2.autoscale.tag.Tag`
        :param tags: The new or updated tags.
        """
        params = {}
        for i, tag in enumerate(tags):
            tag.build_params(params, i + 1)
        return self.get_status('DeleteTags', params, verb='POST')
