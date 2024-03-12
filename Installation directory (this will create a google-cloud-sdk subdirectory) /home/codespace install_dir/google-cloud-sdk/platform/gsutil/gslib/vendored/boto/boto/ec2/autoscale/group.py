# Copyright (c) 2009-2011 Reza Lotun http://reza.lotun.name/
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

from boto.ec2.elb.listelement import ListElement
from boto.resultset import ResultSet
from boto.ec2.autoscale.launchconfig import LaunchConfiguration
from boto.ec2.autoscale.request import Request
from boto.ec2.autoscale.instance import Instance
from boto.ec2.autoscale.tag import Tag


class ProcessType(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.process_name = None

    def __repr__(self):
        return 'ProcessType(%s)' % self.process_name

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'ProcessName':
            self.process_name = value


class SuspendedProcess(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.process_name = None
        self.reason = None

    def __repr__(self):
        return 'SuspendedProcess(%s, %s)' % (self.process_name, self.reason)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'ProcessName':
            self.process_name = value
        elif name == 'SuspensionReason':
            self.reason = value


class EnabledMetric(object):
    def __init__(self, connection=None, metric=None, granularity=None):
        self.connection = connection
        self.metric = metric
        self.granularity = granularity

    def __repr__(self):
        return 'EnabledMetric(%s, %s)' % (self.metric, self.granularity)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Granularity':
            self.granularity = value
        elif name == 'Metric':
            self.metric = value


class TerminationPolicies(list):

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'member':
            self.append(value)


class AutoScalingGroup(object):
    def __init__(self, connection=None, name=None,
                 launch_config=None, availability_zones=None,
                 load_balancers=None, default_cooldown=None,
                 health_check_type=None, health_check_period=None,
                 placement_group=None, vpc_zone_identifier=None,
                 desired_capacity=None, min_size=None, max_size=None,
                 tags=None, termination_policies=None, instance_id=None,
                 **kwargs):
        """
        Creates a new AutoScalingGroup with the specified name.

        You must not have already used up your entire quota of
        AutoScalingGroups in order for this call to be successful. Once the
        creation request is completed, the AutoScalingGroup is ready to be
        used in other calls.

        :type name: str
        :param name: Name of autoscaling group (required).

        :type availability_zones: list
        :param availability_zones: List of availability zones (required).

        :type default_cooldown: int
        :param default_cooldown: Number of seconds after a Scaling Activity
            completes before any further scaling activities can start.

        :type desired_capacity: int
        :param desired_capacity: The desired capacity for the group.

        :type health_check_period: str
        :param health_check_period: Length of time in seconds after a new
            EC2 instance comes into service that Auto Scaling starts
            checking its health.

        :type health_check_type: str
        :param health_check_type: The service you want the health status from,
            Amazon EC2 or Elastic Load Balancer.

        :type launch_config: str or LaunchConfiguration
        :param launch_config: Name of launch configuration (required).

        :type load_balancers: list
        :param load_balancers: List of load balancers.

        :type max_size: int
        :param max_size: Maximum size of group (required).

        :type min_size: int
        :param min_size: Minimum size of group (required).

        :type placement_group: str
        :param placement_group: Physical location of your cluster placement
            group created in Amazon EC2.

        :type vpc_zone_identifier: str or list
        :param vpc_zone_identifier: A comma-separated string or python list of
            the subnet identifiers of the Virtual Private Cloud.

        :type tags: list
        :param tags: List of :class:`boto.ec2.autoscale.tag.Tag`s

        :type termination_policies: list
        :param termination_policies: A list of termination policies. Valid values
            are: "OldestInstance", "NewestInstance", "OldestLaunchConfiguration",
            "ClosestToNextInstanceHour", "Default".  If no value is specified,
            the "Default" value is used.

        :type instance_id: str
        :param instance_id: The ID of the Amazon EC2 instance you want to use
            to create the Auto Scaling group.

        :rtype: :class:`boto.ec2.autoscale.group.AutoScalingGroup`
        :return: An autoscale group.
        """
        self.name = name or kwargs.get('group_name')   # backwards compat
        self.connection = connection
        self.min_size = int(min_size) if min_size is not None else None
        self.max_size = int(max_size) if max_size is not None else None
        self.created_time = None
        # backwards compatibility
        default_cooldown = default_cooldown or kwargs.get('cooldown')
        if default_cooldown is not None:
            default_cooldown = int(default_cooldown)
        self.default_cooldown = default_cooldown
        self.launch_config_name = launch_config
        if launch_config and isinstance(launch_config, LaunchConfiguration):
            self.launch_config_name = launch_config.name
        self.desired_capacity = desired_capacity
        lbs = load_balancers or []
        self.load_balancers = ListElement(lbs)
        zones = availability_zones or []
        self.availability_zones = ListElement(zones)
        self.health_check_period = health_check_period
        self.health_check_type = health_check_type
        self.placement_group = placement_group
        self.autoscaling_group_arn = None
        if type(vpc_zone_identifier) is list:
            vpc_zone_identifier = ','.join(vpc_zone_identifier)
        self.vpc_zone_identifier = vpc_zone_identifier
        self.instances = None
        self.tags = tags or None
        termination_policies = termination_policies or []
        self.termination_policies = ListElement(termination_policies)
        self.instance_id = instance_id

    # backwards compatible access to 'cooldown' param
    def _get_cooldown(self):
        return self.default_cooldown

    def _set_cooldown(self, val):
        self.default_cooldown = val

    cooldown = property(_get_cooldown, _set_cooldown)

    def __repr__(self):
        return 'AutoScaleGroup<%s>' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'Instances':
            self.instances = ResultSet([('member', Instance)])
            return self.instances
        elif name == 'LoadBalancerNames':
            return self.load_balancers
        elif name == 'AvailabilityZones':
            return self.availability_zones
        elif name == 'EnabledMetrics':
            self.enabled_metrics = ResultSet([('member', EnabledMetric)])
            return self.enabled_metrics
        elif name == 'SuspendedProcesses':
            self.suspended_processes = ResultSet([('member', SuspendedProcess)])
            return self.suspended_processes
        elif name == 'Tags':
            self.tags = ResultSet([('member', Tag)])
            return self.tags
        elif name == 'TerminationPolicies':
            return self.termination_policies
        else:
            return

    def endElement(self, name, value, connection):
        if name == 'MinSize':
            self.min_size = int(value)
        elif name == 'AutoScalingGroupARN':
            self.autoscaling_group_arn = value
        elif name == 'CreatedTime':
            self.created_time = value
        elif name == 'DefaultCooldown':
            self.default_cooldown = int(value)
        elif name == 'LaunchConfigurationName':
            self.launch_config_name = value
        elif name == 'DesiredCapacity':
            self.desired_capacity = int(value)
        elif name == 'MaxSize':
            self.max_size = int(value)
        elif name == 'AutoScalingGroupName':
            self.name = value
        elif name == 'PlacementGroup':
            self.placement_group = value
        elif name == 'HealthCheckGracePeriod':
            try:
                self.health_check_period = int(value)
            except ValueError:
                self.health_check_period = None
        elif name == 'HealthCheckType':
            self.health_check_type = value
        elif name == 'VPCZoneIdentifier':
            self.vpc_zone_identifier = value
        elif name == 'InstanceId':
            self.instance_id = value
        else:
            setattr(self, name, value)

    def set_capacity(self, capacity):
        """
        Set the desired capacity for the group.
        """
        params = {'AutoScalingGroupName': self.name,
                  'DesiredCapacity': capacity}
        req = self.connection.get_object('SetDesiredCapacity', params,
                                         Request)
        self.connection.last_request = req
        return req

    def update(self):
        """
        Sync local changes with AutoScaling group.
        """
        return self.connection._update_group('UpdateAutoScalingGroup', self)

    def shutdown_instances(self):
        """
        Convenience method which shuts down all instances associated with
        this group.
        """
        self.min_size = 0
        self.max_size = 0
        self.desired_capacity = 0
        self.update()

    def delete(self, force_delete=False):
        """
        Delete this auto-scaling group if no instances attached or no
        scaling activities in progress.
        """
        return self.connection.delete_auto_scaling_group(self.name,
                                                         force_delete)

    def get_activities(self, activity_ids=None, max_records=50):
        """
        Get all activies for this group.
        """
        return self.connection.get_all_activities(self, activity_ids,
                                                  max_records)

    def put_notification_configuration(self, topic, notification_types):
        """
        Configures an Auto Scaling group to send notifications when
        specified events take place. Valid notification types are:
        'autoscaling:EC2_INSTANCE_LAUNCH',
        'autoscaling:EC2_INSTANCE_LAUNCH_ERROR',
        'autoscaling:EC2_INSTANCE_TERMINATE',
        'autoscaling:EC2_INSTANCE_TERMINATE_ERROR',
        'autoscaling:TEST_NOTIFICATION'
        """
        return self.connection.put_notification_configuration(self,
                                                              topic,
                                                              notification_types)

    def delete_notification_configuration(self, topic):
        """
        Deletes notifications created by put_notification_configuration.
        """
        return self.connection.delete_notification_configuration(self, topic)

    def suspend_processes(self, scaling_processes=None):
        """
        Suspends Auto Scaling processes for an Auto Scaling group.
        """
        return self.connection.suspend_processes(self.name, scaling_processes)

    def resume_processes(self, scaling_processes=None):
        """
        Resumes Auto Scaling processes for an Auto Scaling group.
        """
        return self.connection.resume_processes(self.name, scaling_processes)


class AutoScalingGroupMetric(object):
    def __init__(self, connection=None):

        self.connection = connection
        self.metric = None
        self.granularity = None

    def __repr__(self):
        return 'AutoScalingGroupMetric:%s' % self.metric

    def startElement(self, name, attrs, connection):
        return

    def endElement(self, name, value, connection):
        if name == 'Metric':
            self.metric = value
        elif name == 'Granularity':
            self.granularity = value
        else:
            setattr(self, name, value)
