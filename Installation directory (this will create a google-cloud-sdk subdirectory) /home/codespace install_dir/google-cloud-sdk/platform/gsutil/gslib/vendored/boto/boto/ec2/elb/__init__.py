# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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
"""
This module provides an interface to the Elastic Compute Cloud (EC2)
load balancing service from AWS.
"""
from boto.connection import AWSQueryConnection
from boto.ec2.instanceinfo import InstanceInfo
from boto.ec2.elb.loadbalancer import LoadBalancer, LoadBalancerZones
from boto.ec2.elb.instancestate import InstanceState
from boto.ec2.elb.healthcheck import HealthCheck
from boto.regioninfo import RegionInfo, get_regions, load_regions
from boto.regioninfo import connect
import boto
from boto.compat import six

RegionData = load_regions().get('elasticloadbalancing', {})


def regions():
    """
    Get all available regions for the ELB service.

    :rtype: list
    :return: A list of :class:`boto.RegionInfo` instances
    """
    return get_regions('elasticloadbalancing', connection_cls=ELBConnection)


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.ec2.elb.ELBConnection`.

    :param str region_name: The name of the region to connect to.

    :rtype: :class:`boto.ec2.ELBConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
        name is given
    """
    return connect('elasticloadbalancing', region_name,
                   connection_cls=ELBConnection, **kw_params)


class ELBConnection(AWSQueryConnection):

    APIVersion = boto.config.get('Boto', 'elb_version', '2012-06-01')
    DefaultRegionName = boto.config.get('Boto', 'elb_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get(
        'Boto', 'elb_region_endpoint',
        'elasticloadbalancing.us-east-1.amazonaws.com')

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True, profile_name=None):
        """
        Init method to create a new connection to EC2 Load Balancing Service.

        .. note:: The region argument is overridden by the region specified in
            the boto configuration file.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region
        super(ELBConnection, self).__init__(aws_access_key_id,
                                            aws_secret_access_key,
                                            is_secure, port, proxy, proxy_port,
                                            proxy_user, proxy_pass,
                                            self.region.endpoint, debug,
                                            https_connection_factory, path,
                                            security_token,
                                            validate_certs=validate_certs,
                                            profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def build_list_params(self, params, items, label):
        if isinstance(items, six.string_types):
            items = [items]
        for index, item in enumerate(items):
            params[label % (index + 1)] = item

    def get_all_load_balancers(self, load_balancer_names=None, marker=None):
        """
        Retrieve all load balancers associated with your account.

        :type load_balancer_names: list
        :keyword load_balancer_names: An optional list of load balancer names.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :rtype: :py:class:`boto.resultset.ResultSet`
        :return: A ResultSet containing instances of
            :class:`boto.ec2.elb.loadbalancer.LoadBalancer`
        """
        params = {}
        if load_balancer_names:
            self.build_list_params(params, load_balancer_names,
                                   'LoadBalancerNames.member.%d')

        if marker:
            params['Marker'] = marker

        return self.get_list('DescribeLoadBalancers', params,
                             [('member', LoadBalancer)])

    def create_load_balancer(self, name, zones, listeners=None, subnets=None,
                             security_groups=None, scheme='internet-facing',
                             complex_listeners=None):
        """
        Create a new load balancer for your account. By default the load
        balancer will be created in EC2. To create a load balancer inside a
        VPC, parameter zones must be set to None and subnets must not be None.
        The load balancer will be automatically created under the VPC that
        contains the subnet(s) specified.

        :type name: string
        :param name: The mnemonic name associated with the new load balancer

        :type zones: List of strings
        :param zones: The names of the availability zone(s) to add.

        :type listeners: List of tuples
        :param listeners: Each tuple contains three or four values,
            (LoadBalancerPortNumber, InstancePortNumber, Protocol,
            [SSLCertificateId]) where LoadBalancerPortNumber and
            InstancePortNumber are integer values between 1 and 65535,
            Protocol is a string containing either 'TCP', 'SSL', HTTP', or
            'HTTPS'; SSLCertificateID is the ARN of a AWS IAM
            certificate, and must be specified when doing HTTPS.

        :type subnets: list of strings
        :param subnets: A list of subnet IDs in your VPC to attach to
            your LoadBalancer.

        :type security_groups: list of strings
        :param security_groups: The security groups assigned to your
            LoadBalancer within your VPC.

        :type scheme: string
        :param scheme: The type of a LoadBalancer.  By default, Elastic
            Load Balancing creates an internet-facing LoadBalancer with
            a publicly resolvable DNS name, which resolves to public IP
            addresses.

            Specify the value internal for this option to create an
            internal LoadBalancer with a DNS name that resolves to
            private IP addresses.

            This option is only available for LoadBalancers attached
            to an Amazon VPC.

        :type complex_listeners: List of tuples
        :param complex_listeners: Each tuple contains four or five values,
            (LoadBalancerPortNumber, InstancePortNumber, Protocol,
             InstanceProtocol, SSLCertificateId).

            Where:
                - LoadBalancerPortNumber and InstancePortNumber are integer
                  values between 1 and 65535
                - Protocol and InstanceProtocol is a string containing
                  either 'TCP',
                  'SSL', 'HTTP', or 'HTTPS'
                - SSLCertificateId is the ARN of an SSL certificate loaded into
                  AWS IAM

        :rtype: :class:`boto.ec2.elb.loadbalancer.LoadBalancer`
        :return: The newly created
            :class:`boto.ec2.elb.loadbalancer.LoadBalancer`
        """
        if not listeners and not complex_listeners:
            # Must specify one of the two options
            return None

        params = {'LoadBalancerName': name,
                  'Scheme': scheme}

        # Handle legacy listeners
        if listeners:
            for index, listener in enumerate(listeners):
                i = index + 1
                protocol = listener[2].upper()
                params['Listeners.member.%d.LoadBalancerPort' % i] = listener[0]
                params['Listeners.member.%d.InstancePort' % i] = listener[1]
                params['Listeners.member.%d.Protocol' % i] = listener[2]
                if protocol == 'HTTPS' or protocol == 'SSL':
                    params['Listeners.member.%d.SSLCertificateId' % i] = listener[3]

        # Handle the full listeners
        if complex_listeners:
            for index, listener in enumerate(complex_listeners):
                i = index + 1
                protocol = listener[2].upper()
                InstanceProtocol = listener[3].upper()
                params['Listeners.member.%d.LoadBalancerPort' % i] = listener[0]
                params['Listeners.member.%d.InstancePort' % i] = listener[1]
                params['Listeners.member.%d.Protocol' % i] = listener[2]
                params['Listeners.member.%d.InstanceProtocol' % i] = listener[3]
                if protocol == 'HTTPS' or protocol == 'SSL':
                    params['Listeners.member.%d.SSLCertificateId' % i] = listener[4]

        if zones:
            self.build_list_params(params, zones, 'AvailabilityZones.member.%d')

        if subnets:
            self.build_list_params(params, subnets, 'Subnets.member.%d')

        if security_groups:
            self.build_list_params(params, security_groups,
                                   'SecurityGroups.member.%d')

        load_balancer = self.get_object('CreateLoadBalancer',
                                        params, LoadBalancer)
        load_balancer.name = name
        load_balancer.listeners = listeners
        load_balancer.availability_zones = zones
        load_balancer.subnets = subnets
        load_balancer.security_groups = security_groups
        return load_balancer

    def create_load_balancer_listeners(self, name, listeners=None,
                                       complex_listeners=None):
        """
        Creates a Listener (or group of listeners) for an existing
        Load Balancer

        :type name: string
        :param name: The name of the load balancer to create the listeners for

        :type listeners: List of tuples
        :param listeners: Each tuple contains three or four values,
            (LoadBalancerPortNumber, InstancePortNumber, Protocol,
            [SSLCertificateId]) where LoadBalancerPortNumber and
            InstancePortNumber are integer values between 1 and 65535,
            Protocol is a string containing either 'TCP', 'SSL', HTTP', or
            'HTTPS'; SSLCertificateID is the ARN of a AWS IAM
            certificate, and must be specified when doing HTTPS.

        :type complex_listeners: List of tuples
        :param complex_listeners: Each tuple contains four or five values,
            (LoadBalancerPortNumber, InstancePortNumber, Protocol,
             InstanceProtocol, SSLCertificateId).

            Where:
                - LoadBalancerPortNumber and InstancePortNumber are integer
                  values between 1 and 65535
                - Protocol and InstanceProtocol is a string containing
                  either 'TCP',
                  'SSL', 'HTTP', or 'HTTPS'
                - SSLCertificateId is the ARN of an SSL certificate loaded into
                  AWS IAM

        :return: The status of the request
        """
        if not listeners and not complex_listeners:
            # Must specify one of the two options
            return None

        params = {'LoadBalancerName': name}

        # Handle the simple listeners
        if listeners:
            for index, listener in enumerate(listeners):
                i = index + 1
                protocol = listener[2].upper()
                params['Listeners.member.%d.LoadBalancerPort' % i] = listener[0]
                params['Listeners.member.%d.InstancePort' % i] = listener[1]
                params['Listeners.member.%d.Protocol' % i] = listener[2]
                if protocol == 'HTTPS' or protocol == 'SSL':
                    params['Listeners.member.%d.SSLCertificateId' % i] = listener[3]

        # Handle the full listeners
        if complex_listeners:
            for index, listener in enumerate(complex_listeners):
                i = index + 1
                protocol = listener[2].upper()
                InstanceProtocol = listener[3].upper()
                params['Listeners.member.%d.LoadBalancerPort' % i] = listener[0]
                params['Listeners.member.%d.InstancePort' % i] = listener[1]
                params['Listeners.member.%d.Protocol' % i] = listener[2]
                params['Listeners.member.%d.InstanceProtocol' % i] = listener[3]
                if protocol == 'HTTPS' or protocol == 'SSL':
                    params['Listeners.member.%d.SSLCertificateId' % i] = listener[4]

        return self.get_status('CreateLoadBalancerListeners', params)

    def delete_load_balancer(self, name):
        """
        Delete a Load Balancer from your account.

        :type name: string
        :param name: The name of the Load Balancer to delete
        """
        params = {'LoadBalancerName': name}
        return self.get_status('DeleteLoadBalancer', params)

    def delete_load_balancer_listeners(self, name, ports):
        """
        Deletes a load balancer listener (or group of listeners)

        :type name: string
        :param name: The name of the load balancer to create the listeners for

        :type ports: List int
        :param ports: Each int represents the port on the ELB to be removed

        :return: The status of the request
        """
        params = {'LoadBalancerName': name}
        for index, port in enumerate(ports):
            params['LoadBalancerPorts.member.%d' % (index + 1)] = port
        return self.get_status('DeleteLoadBalancerListeners', params)

    def enable_availability_zones(self, load_balancer_name, zones_to_add):
        """
        Add availability zones to an existing Load Balancer
        All zones must be in the same region as the Load Balancer
        Adding zones that are already registered with the Load Balancer
        has no effect.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type zones: List of strings
        :param zones: The name of the zone(s) to add.

        :rtype: List of strings
        :return: An updated list of zones for this Load Balancer.

        """
        params = {'LoadBalancerName': load_balancer_name}
        self.build_list_params(params, zones_to_add,
                               'AvailabilityZones.member.%d')
        obj = self.get_object('EnableAvailabilityZonesForLoadBalancer',
                              params, LoadBalancerZones)
        return obj.zones

    def disable_availability_zones(self, load_balancer_name, zones_to_remove):
        """
        Remove availability zones from an existing Load Balancer.
        All zones must be in the same region as the Load Balancer.
        Removing zones that are not registered with the Load Balancer
        has no effect.
        You cannot remove all zones from an Load Balancer.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type zones: List of strings
        :param zones: The name of the zone(s) to remove.

        :rtype: List of strings
        :return: An updated list of zones for this Load Balancer.

        """
        params = {'LoadBalancerName': load_balancer_name}
        self.build_list_params(params, zones_to_remove,
                               'AvailabilityZones.member.%d')
        obj = self.get_object('DisableAvailabilityZonesForLoadBalancer',
                              params, LoadBalancerZones)
        return obj.zones

    def modify_lb_attribute(self, load_balancer_name, attribute, value):
        """Changes an attribute of a Load Balancer

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type attribute: string
        :param attribute: The attribute you wish to change.

        * crossZoneLoadBalancing - Boolean (true)
        * connectingSettings - :py:class:`ConnectionSettingAttribute` instance
        * accessLog - :py:class:`AccessLogAttribute` instance
        * connectionDraining - :py:class:`ConnectionDrainingAttribute` instance

        :type value: string
        :param value: The new value for the attribute

        :rtype: bool
        :return: Whether the operation succeeded or not
        """

        bool_reqs = ('crosszoneloadbalancing',)
        if attribute.lower() in bool_reqs:
            if isinstance(value, bool):
                if value:
                    value = 'true'
                else:
                    value = 'false'

        params = {'LoadBalancerName': load_balancer_name}
        if attribute.lower() == 'crosszoneloadbalancing':
            params['LoadBalancerAttributes.CrossZoneLoadBalancing.Enabled'
                   ] = value
        elif attribute.lower() == 'accesslog':
            params['LoadBalancerAttributes.AccessLog.Enabled'] = \
                value.enabled and 'true' or 'false'
            params['LoadBalancerAttributes.AccessLog.S3BucketName'] = \
                value.s3_bucket_name
            params['LoadBalancerAttributes.AccessLog.S3BucketPrefix'] = \
                value.s3_bucket_prefix
            params['LoadBalancerAttributes.AccessLog.EmitInterval'] = \
                value.emit_interval
        elif attribute.lower() == 'connectiondraining':
            params['LoadBalancerAttributes.ConnectionDraining.Enabled'] = \
                value.enabled and 'true' or 'false'
            params['LoadBalancerAttributes.ConnectionDraining.Timeout'] = \
                value.timeout
        elif attribute.lower() == 'connectingsettings':
            params['LoadBalancerAttributes.ConnectionSettings.IdleTimeout'] = \
                value.idle_timeout
        else:
            raise ValueError('InvalidAttribute', attribute)
        return self.get_status('ModifyLoadBalancerAttributes', params,
                               verb='GET')

    def get_all_lb_attributes(self, load_balancer_name):
        """Gets all Attributes of a Load Balancer

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :rtype: boto.ec2.elb.attribute.LbAttributes
        :return: The attribute object of the ELB.
        """
        from boto.ec2.elb.attributes import LbAttributes
        params = {'LoadBalancerName': load_balancer_name}
        return self.get_object('DescribeLoadBalancerAttributes',
                               params, LbAttributes)

    def get_lb_attribute(self, load_balancer_name, attribute):
        """Gets an attribute of a Load Balancer

        This will make an EC2 call for each method call.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type attribute: string
        :param attribute: The attribute you wish to see.

          * accessLog - :py:class:`AccessLogAttribute` instance
          * crossZoneLoadBalancing - Boolean
          * connectingSettings - :py:class:`ConnectionSettingAttribute` instance
          * connectionDraining - :py:class:`ConnectionDrainingAttribute`
            instance

        :rtype: Attribute dependent
        :return: The new value for the attribute
        """
        attributes = self.get_all_lb_attributes(load_balancer_name)
        if attribute.lower() == 'accesslog':
            return attributes.access_log
        if attribute.lower() == 'crosszoneloadbalancing':
            return attributes.cross_zone_load_balancing.enabled
        if attribute.lower() == 'connectiondraining':
            return attributes.connection_draining
        if attribute.lower() == 'connectingsettings':
            return attributes.connecting_settings
        return None

    def register_instances(self, load_balancer_name, instances):
        """
        Add new Instances to an existing Load Balancer.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type instances: List of strings
        :param instances: The instance ID's of the EC2 instances to add.

        :rtype: List of strings
        :return: An updated list of instances for this Load Balancer.

        """
        params = {'LoadBalancerName': load_balancer_name}
        self.build_list_params(params, instances,
                               'Instances.member.%d.InstanceId')
        return self.get_list('RegisterInstancesWithLoadBalancer',
                             params, [('member', InstanceInfo)])

    def deregister_instances(self, load_balancer_name, instances):
        """
        Remove Instances from an existing Load Balancer.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type instances: List of strings
        :param instances: The instance ID's of the EC2 instances to remove.

        :rtype: List of strings
        :return: An updated list of instances for this Load Balancer.

        """
        params = {'LoadBalancerName': load_balancer_name}
        self.build_list_params(params, instances,
                               'Instances.member.%d.InstanceId')
        return self.get_list('DeregisterInstancesFromLoadBalancer',
                             params, [('member', InstanceInfo)])

    def describe_instance_health(self, load_balancer_name, instances=None):
        """
        Get current state of all Instances registered to an Load Balancer.

        :type load_balancer_name: string
        :param load_balancer_name: The name of the Load Balancer

        :type instances: List of strings
        :param instances: The instance ID's of the EC2 instances
                          to return status for.  If not provided,
                          the state of all instances will be returned.

        :rtype: List of :class:`boto.ec2.elb.instancestate.InstanceState`
        :return: list of state info for instances in this Load Balancer.

        """
        params = {'LoadBalancerName': load_balancer_name}
        if instances:
            self.build_list_params(params, instances,
                                   'Instances.member.%d.InstanceId')
        return self.get_list('DescribeInstanceHealth', params,
                             [('member', InstanceState)])

    def configure_health_check(self, name, health_check):
        """
        Define a health check for the EndPoints.

        :type name: string
        :param name: The mnemonic name associated with the load balancer

        :type health_check: :class:`boto.ec2.elb.healthcheck.HealthCheck`
        :param health_check: A HealthCheck object populated with the desired
                             values.

        :rtype: :class:`boto.ec2.elb.healthcheck.HealthCheck`
        :return: The updated :class:`boto.ec2.elb.healthcheck.HealthCheck`
        """
        params = {'LoadBalancerName': name,
                  'HealthCheck.Timeout': health_check.timeout,
                  'HealthCheck.Target': health_check.target,
                  'HealthCheck.Interval': health_check.interval,
                  'HealthCheck.UnhealthyThreshold': health_check.unhealthy_threshold,
                  'HealthCheck.HealthyThreshold': health_check.healthy_threshold}
        return self.get_object('ConfigureHealthCheck', params, HealthCheck)

    def set_lb_listener_SSL_certificate(self, lb_name, lb_port,
                                        ssl_certificate_id):
        """
        Sets the certificate that terminates the specified listener's SSL
        connections. The specified certificate replaces any prior certificate
        that was used on the same LoadBalancer and port.
        """
        params = {'LoadBalancerName': lb_name,
                  'LoadBalancerPort': lb_port,
                  'SSLCertificateId': ssl_certificate_id}
        return self.get_status('SetLoadBalancerListenerSSLCertificate', params)

    def create_app_cookie_stickiness_policy(self, name, lb_name, policy_name):
        """
        Generates a stickiness policy with sticky session lifetimes that follow
        that of an application-generated cookie. This policy can only be
        associated with HTTP listeners.

        This policy is similar to the policy created by
        CreateLBCookieStickinessPolicy, except that the lifetime of the special
        Elastic Load Balancing cookie follows the lifetime of the
        application-generated cookie specified in the policy configuration. The
        load balancer only inserts a new stickiness cookie when the application
        response includes a new application cookie.

        If the application cookie is explicitly removed or expires, the session
        stops being sticky until a new application cookie is issued.
        """
        params = {'CookieName': name,
                  'LoadBalancerName': lb_name,
                  'PolicyName': policy_name}
        return self.get_status('CreateAppCookieStickinessPolicy', params)

    def create_lb_cookie_stickiness_policy(self, cookie_expiration_period,
                                           lb_name, policy_name):
        """
        Generates a stickiness policy with sticky session lifetimes controlled
        by the lifetime of the browser (user-agent) or a specified expiration
        period. This policy can only be associated only with HTTP listeners.

        When a load balancer implements this policy, the load balancer uses a
        special cookie to track the backend server instance for each request.
        When the load balancer receives a request, it first checks to see if
        this cookie is present in the request. If so, the load balancer sends
        the request to the application server specified in the cookie. If not,
        the load balancer sends the request to a server that is chosen based on
        the existing load balancing algorithm.

        A cookie is inserted into the response for binding subsequent requests
        from the same user to that server. The validity of the cookie is based
        on the cookie expiration time, which is specified in the policy
        configuration.

        None may be passed for cookie_expiration_period.
        """
        params = {'LoadBalancerName': lb_name,
                  'PolicyName': policy_name}
        if cookie_expiration_period is not None:
            params['CookieExpirationPeriod'] = cookie_expiration_period
        return self.get_status('CreateLBCookieStickinessPolicy', params)

    def create_lb_policy(self, lb_name, policy_name, policy_type,
                         policy_attributes):
        """
        Creates a new policy that contains the necessary attributes
        depending on the policy type. Policies are settings that are
        saved for your load balancer and that can be applied to the
        front-end listener, or the back-end application server.

        """
        params = {'LoadBalancerName': lb_name,
                  'PolicyName': policy_name,
                  'PolicyTypeName': policy_type}
        for index, (name, value) in enumerate(six.iteritems(policy_attributes), 1):
            params['PolicyAttributes.member.%d.AttributeName' % index] = name
            params['PolicyAttributes.member.%d.AttributeValue' % index] = value
        else:
            params['PolicyAttributes'] = ''
        return self.get_status('CreateLoadBalancerPolicy', params)

    def delete_lb_policy(self, lb_name, policy_name):
        """
        Deletes a policy from the LoadBalancer. The specified policy must not
        be enabled for any listeners.
        """
        params = {'LoadBalancerName': lb_name,
                  'PolicyName': policy_name}
        return self.get_status('DeleteLoadBalancerPolicy', params)

    def set_lb_policies_of_listener(self, lb_name, lb_port, policies):
        """
        Associates, updates, or disables a policy with a listener on the load
        balancer. Currently only zero (0) or one (1) policy can be associated
        with a listener.
        """
        params = {'LoadBalancerName': lb_name,
                  'LoadBalancerPort': lb_port}
        if len(policies):
            self.build_list_params(params, policies, 'PolicyNames.member.%d')
        else:
            params['PolicyNames'] = ''
        return self.get_status('SetLoadBalancerPoliciesOfListener', params)

    def set_lb_policies_of_backend_server(self, lb_name, instance_port,
                                          policies):
        """
        Replaces the current set of policies associated with a port on which
        the back-end server is listening with a new set of policies.
        """
        params = {'LoadBalancerName': lb_name,
                  'InstancePort': instance_port}
        if policies:
            self.build_list_params(params, policies, 'PolicyNames.member.%d')
        else:
            params['PolicyNames'] = ''
        return self.get_status('SetLoadBalancerPoliciesForBackendServer',
                               params)

    def apply_security_groups_to_lb(self, name, security_groups):
        """
        Associates one or more security groups with the load balancer.
        The provided security groups will override any currently applied
        security groups.

        :type name: string
        :param name: The name of the Load Balancer

        :type security_groups: List of strings
        :param security_groups: The name of the security group(s) to add.

        :rtype: List of strings
        :return: An updated list of security groups for this Load Balancer.

        """
        params = {'LoadBalancerName': name}
        self.build_list_params(params, security_groups,
                               'SecurityGroups.member.%d')
        return self.get_list('ApplySecurityGroupsToLoadBalancer',
                             params, None)

    def attach_lb_to_subnets(self, name, subnets):
        """
        Attaches load balancer to one or more subnets.
        Attaching subnets that are already registered with the
        Load Balancer has no effect.

        :type name: string
        :param name: The name of the Load Balancer

        :type subnets: List of strings
        :param subnets: The name of the subnet(s) to add.

        :rtype: List of strings
        :return: An updated list of subnets for this Load Balancer.

        """
        params = {'LoadBalancerName': name}
        self.build_list_params(params, subnets,
                               'Subnets.member.%d')
        return self.get_list('AttachLoadBalancerToSubnets',
                             params, None)

    def detach_lb_from_subnets(self, name, subnets):
        """
        Detaches load balancer from one or more subnets.

        :type name: string
        :param name: The name of the Load Balancer

        :type subnets: List of strings
        :param subnets: The name of the subnet(s) to detach.

        :rtype: List of strings
        :return: An updated list of subnets for this Load Balancer.

        """
        params = {'LoadBalancerName': name}
        self.build_list_params(params, subnets,
                               'Subnets.member.%d')
        return self.get_list('DetachLoadBalancerFromSubnets',
                             params, None)
