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

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.opsworks import exceptions


class OpsWorksConnection(AWSQueryConnection):
    """
    AWS OpsWorks
    Welcome to the AWS OpsWorks API Reference . This guide provides
    descriptions, syntax, and usage examples about AWS OpsWorks
    actions and data types, including common parameters and error
    codes.

    AWS OpsWorks is an application management service that provides an
    integrated experience for overseeing the complete application
    lifecycle. For information about this product, go to the `AWS
    OpsWorks`_ details page.

    **SDKs and CLI**

    The most common way to use the AWS OpsWorks API is by using the
    AWS Command Line Interface (CLI) or by using one of the AWS SDKs
    to implement applications in your preferred language. For more
    information, see:


    + `AWS CLI`_
    + `AWS SDK for Java`_
    + `AWS SDK for .NET`_
    + `AWS SDK for PHP 2`_
    + `AWS SDK for Ruby`_
    + `AWS SDK for Node.js`_
    + `AWS SDK for Python(Boto)`_


    **Endpoints**

    AWS OpsWorks supports only one endpoint, opsworks.us-
    east-1.amazonaws.com (HTTPS), so you must connect to that
    endpoint. You can then use the API to direct AWS OpsWorks to
    create stacks in any AWS Region.

    **Chef Versions**

    When you call CreateStack, CloneStack, or UpdateStack we recommend
    you use the `ConfigurationManager` parameter to specify the Chef
    version, 0.9, 11.4, or 11.10. The default value is currently
    11.10. For more information, see `Chef Versions`_.

    You can still specify Chef 0.9 for your stack, but new features
    are not available for Chef 0.9 stacks, and support is scheduled to
    end on July 24, 2014. We do not recommend using Chef 0.9 for new
    stacks, and we recommend migrating your existing Chef 0.9 stacks
    to Chef 11.10 as soon as possible.
    """
    APIVersion = "2013-02-18"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "opsworks.us-east-1.amazonaws.com"
    ServiceName = "OpsWorks"
    TargetPrefix = "OpsWorks_20130218"
    ResponseError = JSONResponseError

    _faults = {
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "ValidationException": exceptions.ValidationException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(OpsWorksConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def assign_instance(self, instance_id, layer_ids):
        """
        Assign a registered instance to a custom layer. You cannot use
        this action with instances that were created with AWS
        OpsWorks.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        :type layer_ids: list
        :param layer_ids: The layer ID, which must correspond to a custom
            layer. You cannot assign a registered instance to a built-in layer.

        """
        params = {
            'InstanceId': instance_id,
            'LayerIds': layer_ids,
        }
        return self.make_request(action='AssignInstance',
                                 body=json.dumps(params))

    def assign_volume(self, volume_id, instance_id=None):
        """
        Assigns one of the stack's registered Amazon EBS volumes to a
        specified instance. The volume must first be registered with
        the stack by calling RegisterVolume. For more information, see
        `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type volume_id: string
        :param volume_id: The volume ID.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'VolumeId': volume_id, }
        if instance_id is not None:
            params['InstanceId'] = instance_id
        return self.make_request(action='AssignVolume',
                                 body=json.dumps(params))

    def associate_elastic_ip(self, elastic_ip, instance_id=None):
        """
        Associates one of the stack's registered Elastic IP addresses
        with a specified instance. The address must first be
        registered with the stack by calling RegisterElasticIp. For
        more information, see `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_ip: string
        :param elastic_ip: The Elastic IP address.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'ElasticIp': elastic_ip, }
        if instance_id is not None:
            params['InstanceId'] = instance_id
        return self.make_request(action='AssociateElasticIp',
                                 body=json.dumps(params))

    def attach_elastic_load_balancer(self, elastic_load_balancer_name,
                                     layer_id):
        """
        Attaches an Elastic Load Balancing load balancer to a
        specified layer. For more information, see `Elastic Load
        Balancing`_.


        You must create the Elastic Load Balancing instance
        separately, by using the Elastic Load Balancing console, API,
        or CLI. For more information, see ` Elastic Load Balancing
        Developer Guide`_.


        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_load_balancer_name: string
        :param elastic_load_balancer_name: The Elastic Load Balancing
            instance's name.

        :type layer_id: string
        :param layer_id: The ID of the layer that the Elastic Load Balancing
            instance is to be attached to.

        """
        params = {
            'ElasticLoadBalancerName': elastic_load_balancer_name,
            'LayerId': layer_id,
        }
        return self.make_request(action='AttachElasticLoadBalancer',
                                 body=json.dumps(params))

    def clone_stack(self, source_stack_id, service_role_arn, name=None,
                    region=None, vpc_id=None, attributes=None,
                    default_instance_profile_arn=None, default_os=None,
                    hostname_theme=None, default_availability_zone=None,
                    default_subnet_id=None, custom_json=None,
                    configuration_manager=None, chef_configuration=None,
                    use_custom_cookbooks=None,
                    use_opsworks_security_groups=None,
                    custom_cookbooks_source=None, default_ssh_key_name=None,
                    clone_permissions=None, clone_app_ids=None,
                    default_root_device_type=None):
        """
        Creates a clone of a specified stack. For more information,
        see `Clone a Stack`_.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type source_stack_id: string
        :param source_stack_id: The source stack ID.

        :type name: string
        :param name: The cloned stack name.

        :type region: string
        :param region: The cloned stack AWS region, such as "us-east-1". For
            more information about AWS regions, see `Regions and Endpoints`_.

        :type vpc_id: string
        :param vpc_id: The ID of the VPC that the cloned stack is to be
            launched into. It must be in the specified region. All instances
            are launched into this VPC, and you cannot change the ID later.

        + If your account supports EC2 Classic, the default value is no VPC.
        + If your account does not support EC2 Classic, the default value is
              the default VPC for the specified region.


        If the VPC ID corresponds to a default VPC and you have specified
            either the `DefaultAvailabilityZone` or the `DefaultSubnetId`
            parameter only, AWS OpsWorks infers the value of the other
            parameter. If you specify neither parameter, AWS OpsWorks sets
            these parameters to the first valid Availability Zone for the
            specified region and the corresponding default VPC subnet ID,
            respectively.

        If you specify a nondefault VPC ID, note the following:


        + It must belong to a VPC in your account that is in the specified
              region.
        + You must specify a value for `DefaultSubnetId`.


        For more information on how to use AWS OpsWorks with a VPC, see
            `Running a Stack in a VPC`_. For more information on default VPC
            and EC2 Classic, see `Supported Platforms`_.

        :type attributes: map
        :param attributes: A list of stack attributes and values as key/value
            pairs to be added to the cloned stack.

        :type service_role_arn: string
        :param service_role_arn:
        The stack AWS Identity and Access Management (IAM) role, which allows
            AWS OpsWorks to work with AWS resources on your behalf. You must
            set this parameter to the Amazon Resource Name (ARN) for an
            existing IAM role. If you create a stack by using the AWS OpsWorks
            console, it creates the role for you. You can obtain an existing
            stack's IAM ARN programmatically by calling DescribePermissions.
            For more information about IAM ARNs, see `Using Identifiers`_.


        You must set this parameter to a valid service role ARN or the action
            will fail; there is no default value. You can specify the source
            stack's service role ARN, if you prefer, but you must do so
            explicitly.

        :type default_instance_profile_arn: string
        :param default_instance_profile_arn: The ARN of an IAM profile that is
            the default profile for all of the stack's EC2 instances. For more
            information about IAM ARNs, see `Using Identifiers`_.

        :type default_os: string
        :param default_os: The stacks's operating system, which must be set to
            one of the following.

        + Standard operating systems: an Amazon Linux version such as `Amazon
              Linux 2014.09`, `Ubuntu 12.04 LTS`, or `Ubuntu 14.04 LTS`.
        + Custom AMIs: `Custom`. You specify the custom AMI you want to use
              when you create instances.


        The default option is the current Amazon Linux version.

        :type hostname_theme: string
        :param hostname_theme: The stack's host name theme, with spaces are
            replaced by underscores. The theme is used to generate host names
            for the stack's instances. By default, `HostnameTheme` is set to
            `Layer_Dependent`, which creates host names by appending integers
            to the layer's short name. The other themes are:

        + `Baked_Goods`
        + `Clouds`
        + `European_Cities`
        + `Fruits`
        + `Greek_Deities`
        + `Legendary_Creatures_from_Japan`
        + `Planets_and_Moons`
        + `Roman_Deities`
        + `Scottish_Islands`
        + `US_Cities`
        + `Wild_Cats`


        To obtain a generated host name, call `GetHostNameSuggestion`, which
            returns a host name based on the current theme.

        :type default_availability_zone: string
        :param default_availability_zone: The cloned stack's default
            Availability Zone, which must be in the specified region. For more
            information, see `Regions and Endpoints`_. If you also specify a
            value for `DefaultSubnetId`, the subnet must be in the same zone.
            For more information, see the `VpcId` parameter description.

        :type default_subnet_id: string
        :param default_subnet_id: The stack's default VPC subnet ID. This
            parameter is required if you specify a value for the `VpcId`
            parameter. All instances are launched into this subnet unless you
            specify otherwise when you create the instance. If you also specify
            a value for `DefaultAvailabilityZone`, the subnet must be in that
            zone. For information on default values and when this parameter is
            required, see the `VpcId` parameter description.

        :type custom_json: string
        :param custom_json: A string that contains user-defined, custom JSON.
            It is used to override the corresponding default stack
            configuration JSON values. The string should be in the following
            format and must escape characters such as '"'.:
        `"{\"key1\": \"value1\", \"key2\": \"value2\",...}"`

        For more information on custom JSON, see `Use Custom JSON to Modify the
            Stack Configuration JSON`_

        :type configuration_manager: dict
        :param configuration_manager: The configuration manager. When you clone
            a stack we recommend that you use the configuration manager to
            specify the Chef version, 0.9, 11.4, or 11.10. The default value is
            currently 11.4.

        :type chef_configuration: dict
        :param chef_configuration: A `ChefConfiguration` object that specifies
            whether to enable Berkshelf and the Berkshelf version on Chef 11.10
            stacks. For more information, see `Create a New Stack`_.

        :type use_custom_cookbooks: boolean
        :param use_custom_cookbooks: Whether to use custom cookbooks.

        :type use_opsworks_security_groups: boolean
        :param use_opsworks_security_groups: Whether to associate the AWS
            OpsWorks built-in security groups with the stack's layers.
        AWS OpsWorks provides a standard set of built-in security groups, one
            for each layer, which are associated with layers by default. With
            `UseOpsworksSecurityGroups` you can instead provide your own custom
            security groups. `UseOpsworksSecurityGroups` has the following
            settings:


        + True - AWS OpsWorks automatically associates the appropriate built-in
              security group with each layer (default setting). You can associate
              additional security groups with a layer after you create it but you
              cannot delete the built-in security group.
        + False - AWS OpsWorks does not associate built-in security groups with
              layers. You must create appropriate EC2 security groups and
              associate a security group with each layer that you create.
              However, you can still manually associate a built-in security group
              with a layer on creation; custom security groups are required only
              for those layers that need custom settings.


        For more information, see `Create a New Stack`_.

        :type custom_cookbooks_source: dict
        :param custom_cookbooks_source: Contains the information required to
            retrieve an app or cookbook from a repository. For more
            information, see `Creating Apps`_ or `Custom Recipes and
            Cookbooks`_.

        :type default_ssh_key_name: string
        :param default_ssh_key_name: A default SSH key for the stack instances.
            You can override this value when you create or update an instance.

        :type clone_permissions: boolean
        :param clone_permissions: Whether to clone the source stack's
            permissions.

        :type clone_app_ids: list
        :param clone_app_ids: A list of source stack app IDs to be included in
            the cloned stack.

        :type default_root_device_type: string
        :param default_root_device_type: The default root device type. This
            value is used by default for all instances in the cloned stack, but
            you can override it when you create an instance. For more
            information, see `Storage for the Root Device`_.

        """
        params = {
            'SourceStackId': source_stack_id,
            'ServiceRoleArn': service_role_arn,
        }
        if name is not None:
            params['Name'] = name
        if region is not None:
            params['Region'] = region
        if vpc_id is not None:
            params['VpcId'] = vpc_id
        if attributes is not None:
            params['Attributes'] = attributes
        if default_instance_profile_arn is not None:
            params['DefaultInstanceProfileArn'] = default_instance_profile_arn
        if default_os is not None:
            params['DefaultOs'] = default_os
        if hostname_theme is not None:
            params['HostnameTheme'] = hostname_theme
        if default_availability_zone is not None:
            params['DefaultAvailabilityZone'] = default_availability_zone
        if default_subnet_id is not None:
            params['DefaultSubnetId'] = default_subnet_id
        if custom_json is not None:
            params['CustomJson'] = custom_json
        if configuration_manager is not None:
            params['ConfigurationManager'] = configuration_manager
        if chef_configuration is not None:
            params['ChefConfiguration'] = chef_configuration
        if use_custom_cookbooks is not None:
            params['UseCustomCookbooks'] = use_custom_cookbooks
        if use_opsworks_security_groups is not None:
            params['UseOpsworksSecurityGroups'] = use_opsworks_security_groups
        if custom_cookbooks_source is not None:
            params['CustomCookbooksSource'] = custom_cookbooks_source
        if default_ssh_key_name is not None:
            params['DefaultSshKeyName'] = default_ssh_key_name
        if clone_permissions is not None:
            params['ClonePermissions'] = clone_permissions
        if clone_app_ids is not None:
            params['CloneAppIds'] = clone_app_ids
        if default_root_device_type is not None:
            params['DefaultRootDeviceType'] = default_root_device_type
        return self.make_request(action='CloneStack',
                                 body=json.dumps(params))

    def create_app(self, stack_id, name, type, shortname=None,
                   description=None, data_sources=None, app_source=None,
                   domains=None, enable_ssl=None, ssl_configuration=None,
                   attributes=None, environment=None):
        """
        Creates an app for a specified stack. For more information,
        see `Creating Apps`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type shortname: string
        :param shortname: The app's short name.

        :type name: string
        :param name: The app name.

        :type description: string
        :param description: A description of the app.

        :type data_sources: list
        :param data_sources: The app's data source.

        :type type: string
        :param type: The app type. Each supported type is associated with a
            particular layer. For example, PHP applications are associated with
            a PHP layer. AWS OpsWorks deploys an application to those instances
            that are members of the corresponding layer.

        :type app_source: dict
        :param app_source: A `Source` object that specifies the app repository.

        :type domains: list
        :param domains: The app virtual host settings, with multiple domains
            separated by commas. For example: `'www.example.com, example.com'`

        :type enable_ssl: boolean
        :param enable_ssl: Whether to enable SSL for the app.

        :type ssl_configuration: dict
        :param ssl_configuration: An `SslConfiguration` object with the SSL
            configuration.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type environment: list
        :param environment:
        An array of `EnvironmentVariable` objects that specify environment
            variables to be associated with the app. You can specify up to ten
            environment variables. After you deploy the app, these variables
            are defined on the associated app server instance.

        This parameter is supported only by Chef 11.10 stacks. If you have
            specified one or more environment variables, you cannot modify the
            stack's Chef version.

        """
        params = {'StackId': stack_id, 'Name': name, 'Type': type, }
        if shortname is not None:
            params['Shortname'] = shortname
        if description is not None:
            params['Description'] = description
        if data_sources is not None:
            params['DataSources'] = data_sources
        if app_source is not None:
            params['AppSource'] = app_source
        if domains is not None:
            params['Domains'] = domains
        if enable_ssl is not None:
            params['EnableSsl'] = enable_ssl
        if ssl_configuration is not None:
            params['SslConfiguration'] = ssl_configuration
        if attributes is not None:
            params['Attributes'] = attributes
        if environment is not None:
            params['Environment'] = environment
        return self.make_request(action='CreateApp',
                                 body=json.dumps(params))

    def create_deployment(self, stack_id, command, app_id=None,
                          instance_ids=None, comment=None, custom_json=None):
        """
        Runs deployment or stack commands. For more information, see
        `Deploying Apps`_ and `Run Stack Commands`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Deploy or Manage permissions level for the stack, or an
        attached policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type app_id: string
        :param app_id: The app ID. This parameter is required for app
            deployments, but not for other deployment commands.

        :type instance_ids: list
        :param instance_ids: The instance IDs for the deployment targets.

        :type command: dict
        :param command: A `DeploymentCommand` object that specifies the
            deployment command and any associated arguments.

        :type comment: string
        :param comment: A user-defined comment.

        :type custom_json: string
        :param custom_json: A string that contains user-defined, custom JSON.
            It is used to override the corresponding default stack
            configuration JSON values. The string should be in the following
            format and must escape characters such as '"'.:
        `"{\"key1\": \"value1\", \"key2\": \"value2\",...}"`

        For more information on custom JSON, see `Use Custom JSON to Modify the
            Stack Configuration JSON`_.

        """
        params = {'StackId': stack_id, 'Command': command, }
        if app_id is not None:
            params['AppId'] = app_id
        if instance_ids is not None:
            params['InstanceIds'] = instance_ids
        if comment is not None:
            params['Comment'] = comment
        if custom_json is not None:
            params['CustomJson'] = custom_json
        return self.make_request(action='CreateDeployment',
                                 body=json.dumps(params))

    def create_instance(self, stack_id, layer_ids, instance_type,
                        auto_scaling_type=None, hostname=None, os=None,
                        ami_id=None, ssh_key_name=None,
                        availability_zone=None, virtualization_type=None,
                        subnet_id=None, architecture=None,
                        root_device_type=None, install_updates_on_boot=None,
                        ebs_optimized=None):
        """
        Creates an instance in a specified stack. For more
        information, see `Adding an Instance to a Layer`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type layer_ids: list
        :param layer_ids: An array that contains the instance layer IDs.

        :type instance_type: string
        :param instance_type: The instance type. AWS OpsWorks supports all
            instance types except Cluster Compute, Cluster GPU, and High Memory
            Cluster. For more information, see `Instance Families and Types`_.
            The parameter values that you use to specify the various types are
            in the API Name column of the Available Instance Types table.

        :type auto_scaling_type: string
        :param auto_scaling_type: For load-based or time-based instances, the
            type.

        :type hostname: string
        :param hostname: The instance host name.

        :type os: string
        :param os: The instance's operating system, which must be set to one of
            the following.

        + Standard operating systems: an Amazon Linux version such as `Amazon
              Linux 2014.09`, `Ubuntu 12.04 LTS`, or `Ubuntu 14.04 LTS`.
        + Custom AMIs: `Custom`


        The default option is the current Amazon Linux version. If you set this
            parameter to `Custom`, you must use the CreateInstance action's
            AmiId parameter to specify the custom AMI that you want to use. For
            more information on the standard operating systems, see `Operating
            Systems`_For more information on how to use custom AMIs with
            OpsWorks, see `Using Custom AMIs`_.

        :type ami_id: string
        :param ami_id:
        A custom AMI ID to be used to create the instance. The AMI should be
            based on one of the standard AWS OpsWorks AMIs: Amazon Linux,
            Ubuntu 12.04 LTS, or Ubuntu 14.04 LTS. For more information, see
            `Instances`_.

        If you specify a custom AMI, you must set `Os` to `Custom`.

        :type ssh_key_name: string
        :param ssh_key_name: The instance SSH key name.

        :type availability_zone: string
        :param availability_zone: The instance Availability Zone. For more
            information, see `Regions and Endpoints`_.

        :type virtualization_type: string
        :param virtualization_type: The instance's virtualization type,
            `paravirtual` or `hvm`.

        :type subnet_id: string
        :param subnet_id: The ID of the instance's subnet. If the stack is
            running in a VPC, you can use this parameter to override the
            stack's default subnet ID value and direct AWS OpsWorks to launch
            the instance in a different subnet.

        :type architecture: string
        :param architecture: The instance architecture. The default option is
            `x86_64`. Instance types do not necessarily support both
            architectures. For a list of the architectures that are supported
            by the different instance types, see `Instance Families and
            Types`_.

        :type root_device_type: string
        :param root_device_type: The instance root device type. For more
            information, see `Storage for the Root Device`_.

        :type install_updates_on_boot: boolean
        :param install_updates_on_boot:
        Whether to install operating system and package updates when the
            instance boots. The default value is `True`. To control when
            updates are installed, set this value to `False`. You must then
            update your instances manually by using CreateDeployment to run the
            `update_dependencies` stack command or manually running `yum`
            (Amazon Linux) or `apt-get` (Ubuntu) on the instances.


        We strongly recommend using the default value of `True` to ensure that
            your instances have the latest security updates.

        :type ebs_optimized: boolean
        :param ebs_optimized: Whether to create an Amazon EBS-optimized
            instance.

        """
        params = {
            'StackId': stack_id,
            'LayerIds': layer_ids,
            'InstanceType': instance_type,
        }
        if auto_scaling_type is not None:
            params['AutoScalingType'] = auto_scaling_type
        if hostname is not None:
            params['Hostname'] = hostname
        if os is not None:
            params['Os'] = os
        if ami_id is not None:
            params['AmiId'] = ami_id
        if ssh_key_name is not None:
            params['SshKeyName'] = ssh_key_name
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if virtualization_type is not None:
            params['VirtualizationType'] = virtualization_type
        if subnet_id is not None:
            params['SubnetId'] = subnet_id
        if architecture is not None:
            params['Architecture'] = architecture
        if root_device_type is not None:
            params['RootDeviceType'] = root_device_type
        if install_updates_on_boot is not None:
            params['InstallUpdatesOnBoot'] = install_updates_on_boot
        if ebs_optimized is not None:
            params['EbsOptimized'] = ebs_optimized
        return self.make_request(action='CreateInstance',
                                 body=json.dumps(params))

    def create_layer(self, stack_id, type, name, shortname, attributes=None,
                     custom_instance_profile_arn=None,
                     custom_security_group_ids=None, packages=None,
                     volume_configurations=None, enable_auto_healing=None,
                     auto_assign_elastic_ips=None,
                     auto_assign_public_ips=None, custom_recipes=None,
                     install_updates_on_boot=None,
                     use_ebs_optimized_instances=None,
                     lifecycle_event_configuration=None):
        """
        Creates a layer. For more information, see `How to Create a
        Layer`_.


        You should use **CreateLayer** for noncustom layer types such
        as PHP App Server only if the stack does not have an existing
        layer of that type. A stack can have at most one instance of
        each noncustom layer; if you attempt to create a second
        instance, **CreateLayer** fails. A stack can have an arbitrary
        number of custom layers, so you can call **CreateLayer** as
        many times as you like for that layer type.


        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The layer stack ID.

        :type type: string
        :param type: The layer type. A stack cannot have more than one built-in
            layer of the same type. It can have any number of custom layers.

        :type name: string
        :param name: The layer name, which is used by the console.

        :type shortname: string
        :param shortname: The layer short name, which is used internally by AWS
            OpsWorks and by Chef recipes. The short name is also used as the
            name for the directory where your app files are installed. It can
            have a maximum of 200 characters, which are limited to the
            alphanumeric characters, '-', '_', and '.'.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type custom_instance_profile_arn: string
        :param custom_instance_profile_arn: The ARN of an IAM profile that to
            be used for the layer's EC2 instances. For more information about
            IAM ARNs, see `Using Identifiers`_.

        :type custom_security_group_ids: list
        :param custom_security_group_ids: An array containing the layer custom
            security group IDs.

        :type packages: list
        :param packages: An array of `Package` objects that describe the layer
            packages.

        :type volume_configurations: list
        :param volume_configurations: A `VolumeConfigurations` object that
            describes the layer's Amazon EBS volumes.

        :type enable_auto_healing: boolean
        :param enable_auto_healing: Whether to disable auto healing for the
            layer.

        :type auto_assign_elastic_ips: boolean
        :param auto_assign_elastic_ips: Whether to automatically assign an
            `Elastic IP address`_ to the layer's instances. For more
            information, see `How to Edit a Layer`_.

        :type auto_assign_public_ips: boolean
        :param auto_assign_public_ips: For stacks that are running in a VPC,
            whether to automatically assign a public IP address to the layer's
            instances. For more information, see `How to Edit a Layer`_.

        :type custom_recipes: dict
        :param custom_recipes: A `LayerCustomRecipes` object that specifies the
            layer custom recipes.

        :type install_updates_on_boot: boolean
        :param install_updates_on_boot:
        Whether to install operating system and package updates when the
            instance boots. The default value is `True`. To control when
            updates are installed, set this value to `False`. You must then
            update your instances manually by using CreateDeployment to run the
            `update_dependencies` stack command or manually running `yum`
            (Amazon Linux) or `apt-get` (Ubuntu) on the instances.


        We strongly recommend using the default value of `True`, to ensure that
            your instances have the latest security updates.

        :type use_ebs_optimized_instances: boolean
        :param use_ebs_optimized_instances: Whether to use Amazon EBS-optimized
            instances.

        :type lifecycle_event_configuration: dict
        :param lifecycle_event_configuration: A LifeCycleEventConfiguration
            object that you can use to configure the Shutdown event to specify
            an execution timeout and enable or disable Elastic Load Balancer
            connection draining.

        """
        params = {
            'StackId': stack_id,
            'Type': type,
            'Name': name,
            'Shortname': shortname,
        }
        if attributes is not None:
            params['Attributes'] = attributes
        if custom_instance_profile_arn is not None:
            params['CustomInstanceProfileArn'] = custom_instance_profile_arn
        if custom_security_group_ids is not None:
            params['CustomSecurityGroupIds'] = custom_security_group_ids
        if packages is not None:
            params['Packages'] = packages
        if volume_configurations is not None:
            params['VolumeConfigurations'] = volume_configurations
        if enable_auto_healing is not None:
            params['EnableAutoHealing'] = enable_auto_healing
        if auto_assign_elastic_ips is not None:
            params['AutoAssignElasticIps'] = auto_assign_elastic_ips
        if auto_assign_public_ips is not None:
            params['AutoAssignPublicIps'] = auto_assign_public_ips
        if custom_recipes is not None:
            params['CustomRecipes'] = custom_recipes
        if install_updates_on_boot is not None:
            params['InstallUpdatesOnBoot'] = install_updates_on_boot
        if use_ebs_optimized_instances is not None:
            params['UseEbsOptimizedInstances'] = use_ebs_optimized_instances
        if lifecycle_event_configuration is not None:
            params['LifecycleEventConfiguration'] = lifecycle_event_configuration
        return self.make_request(action='CreateLayer',
                                 body=json.dumps(params))

    def create_stack(self, name, region, service_role_arn,
                     default_instance_profile_arn, vpc_id=None,
                     attributes=None, default_os=None, hostname_theme=None,
                     default_availability_zone=None, default_subnet_id=None,
                     custom_json=None, configuration_manager=None,
                     chef_configuration=None, use_custom_cookbooks=None,
                     use_opsworks_security_groups=None,
                     custom_cookbooks_source=None, default_ssh_key_name=None,
                     default_root_device_type=None):
        """
        Creates a new stack. For more information, see `Create a New
        Stack`_.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type name: string
        :param name: The stack name.

        :type region: string
        :param region: The stack AWS region, such as "us-east-1". For more
            information about Amazon regions, see `Regions and Endpoints`_.

        :type vpc_id: string
        :param vpc_id: The ID of the VPC that the stack is to be launched into.
            It must be in the specified region. All instances are launched into
            this VPC, and you cannot change the ID later.

        + If your account supports EC2 Classic, the default value is no VPC.
        + If your account does not support EC2 Classic, the default value is
              the default VPC for the specified region.


        If the VPC ID corresponds to a default VPC and you have specified
            either the `DefaultAvailabilityZone` or the `DefaultSubnetId`
            parameter only, AWS OpsWorks infers the value of the other
            parameter. If you specify neither parameter, AWS OpsWorks sets
            these parameters to the first valid Availability Zone for the
            specified region and the corresponding default VPC subnet ID,
            respectively.

        If you specify a nondefault VPC ID, note the following:


        + It must belong to a VPC in your account that is in the specified
              region.
        + You must specify a value for `DefaultSubnetId`.


        For more information on how to use AWS OpsWorks with a VPC, see
            `Running a Stack in a VPC`_. For more information on default VPC
            and EC2 Classic, see `Supported Platforms`_.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type service_role_arn: string
        :param service_role_arn: The stack AWS Identity and Access Management
            (IAM) role, which allows AWS OpsWorks to work with AWS resources on
            your behalf. You must set this parameter to the Amazon Resource
            Name (ARN) for an existing IAM role. For more information about IAM
            ARNs, see `Using Identifiers`_.

        :type default_instance_profile_arn: string
        :param default_instance_profile_arn: The ARN of an IAM profile that is
            the default profile for all of the stack's EC2 instances. For more
            information about IAM ARNs, see `Using Identifiers`_.

        :type default_os: string
        :param default_os: The stack's operating system, which must be set to
            one of the following.

        + Standard operating systems: an Amazon Linux version such as `Amazon
              Linux 2014.09`, `Ubuntu 12.04 LTS`, or `Ubuntu 14.04 LTS`.
        + Custom AMIs: `Custom`. You specify the custom AMI you want to use
              when you create instances.


        The default option is the current Amazon Linux version.

        :type hostname_theme: string
        :param hostname_theme: The stack's host name theme, with spaces are
            replaced by underscores. The theme is used to generate host names
            for the stack's instances. By default, `HostnameTheme` is set to
            `Layer_Dependent`, which creates host names by appending integers
            to the layer's short name. The other themes are:

        + `Baked_Goods`
        + `Clouds`
        + `European_Cities`
        + `Fruits`
        + `Greek_Deities`
        + `Legendary_Creatures_from_Japan`
        + `Planets_and_Moons`
        + `Roman_Deities`
        + `Scottish_Islands`
        + `US_Cities`
        + `Wild_Cats`


        To obtain a generated host name, call `GetHostNameSuggestion`, which
            returns a host name based on the current theme.

        :type default_availability_zone: string
        :param default_availability_zone: The stack's default Availability
            Zone, which must be in the specified region. For more information,
            see `Regions and Endpoints`_. If you also specify a value for
            `DefaultSubnetId`, the subnet must be in the same zone. For more
            information, see the `VpcId` parameter description.

        :type default_subnet_id: string
        :param default_subnet_id: The stack's default VPC subnet ID. This
            parameter is required if you specify a value for the `VpcId`
            parameter. All instances are launched into this subnet unless you
            specify otherwise when you create the instance. If you also specify
            a value for `DefaultAvailabilityZone`, the subnet must be in that
            zone. For information on default values and when this parameter is
            required, see the `VpcId` parameter description.

        :type custom_json: string
        :param custom_json: A string that contains user-defined, custom JSON.
            It is used to override the corresponding default stack
            configuration JSON values. The string should be in the following
            format and must escape characters such as '"'.:
        `"{\"key1\": \"value1\", \"key2\": \"value2\",...}"`

        For more information on custom JSON, see `Use Custom JSON to Modify the
            Stack Configuration JSON`_.

        :type configuration_manager: dict
        :param configuration_manager: The configuration manager. When you clone
            a stack we recommend that you use the configuration manager to
            specify the Chef version, 0.9, 11.4, or 11.10. The default value is
            currently 11.4.

        :type chef_configuration: dict
        :param chef_configuration: A `ChefConfiguration` object that specifies
            whether to enable Berkshelf and the Berkshelf version on Chef 11.10
            stacks. For more information, see `Create a New Stack`_.

        :type use_custom_cookbooks: boolean
        :param use_custom_cookbooks: Whether the stack uses custom cookbooks.

        :type use_opsworks_security_groups: boolean
        :param use_opsworks_security_groups: Whether to associate the AWS
            OpsWorks built-in security groups with the stack's layers.
        AWS OpsWorks provides a standard set of built-in security groups, one
            for each layer, which are associated with layers by default. With
            `UseOpsworksSecurityGroups` you can instead provide your own custom
            security groups. `UseOpsworksSecurityGroups` has the following
            settings:


        + True - AWS OpsWorks automatically associates the appropriate built-in
              security group with each layer (default setting). You can associate
              additional security groups with a layer after you create it but you
              cannot delete the built-in security group.
        + False - AWS OpsWorks does not associate built-in security groups with
              layers. You must create appropriate EC2 security groups and
              associate a security group with each layer that you create.
              However, you can still manually associate a built-in security group
              with a layer on creation; custom security groups are required only
              for those layers that need custom settings.


        For more information, see `Create a New Stack`_.

        :type custom_cookbooks_source: dict
        :param custom_cookbooks_source: Contains the information required to
            retrieve an app or cookbook from a repository. For more
            information, see `Creating Apps`_ or `Custom Recipes and
            Cookbooks`_.

        :type default_ssh_key_name: string
        :param default_ssh_key_name: A default SSH key for the stack instances.
            You can override this value when you create or update an instance.

        :type default_root_device_type: string
        :param default_root_device_type: The default root device type. This
            value is used by default for all instances in the stack, but you
            can override it when you create an instance. The default option is
            `instance-store`. For more information, see `Storage for the Root
            Device`_.

        """
        params = {
            'Name': name,
            'Region': region,
            'ServiceRoleArn': service_role_arn,
            'DefaultInstanceProfileArn': default_instance_profile_arn,
        }
        if vpc_id is not None:
            params['VpcId'] = vpc_id
        if attributes is not None:
            params['Attributes'] = attributes
        if default_os is not None:
            params['DefaultOs'] = default_os
        if hostname_theme is not None:
            params['HostnameTheme'] = hostname_theme
        if default_availability_zone is not None:
            params['DefaultAvailabilityZone'] = default_availability_zone
        if default_subnet_id is not None:
            params['DefaultSubnetId'] = default_subnet_id
        if custom_json is not None:
            params['CustomJson'] = custom_json
        if configuration_manager is not None:
            params['ConfigurationManager'] = configuration_manager
        if chef_configuration is not None:
            params['ChefConfiguration'] = chef_configuration
        if use_custom_cookbooks is not None:
            params['UseCustomCookbooks'] = use_custom_cookbooks
        if use_opsworks_security_groups is not None:
            params['UseOpsworksSecurityGroups'] = use_opsworks_security_groups
        if custom_cookbooks_source is not None:
            params['CustomCookbooksSource'] = custom_cookbooks_source
        if default_ssh_key_name is not None:
            params['DefaultSshKeyName'] = default_ssh_key_name
        if default_root_device_type is not None:
            params['DefaultRootDeviceType'] = default_root_device_type
        return self.make_request(action='CreateStack',
                                 body=json.dumps(params))

    def create_user_profile(self, iam_user_arn, ssh_username=None,
                            ssh_public_key=None, allow_self_management=None):
        """
        Creates a new user profile.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type iam_user_arn: string
        :param iam_user_arn: The user's IAM ARN.

        :type ssh_username: string
        :param ssh_username: The user's SSH user name. The allowable characters
            are [a-z], [A-Z], [0-9], '-', and '_'. If the specified name
            includes other punctuation marks, AWS OpsWorks removes them. For
            example, `my.name` will be changed to `myname`. If you do not
            specify an SSH user name, AWS OpsWorks generates one from the IAM
            user name.

        :type ssh_public_key: string
        :param ssh_public_key: The user's public SSH key.

        :type allow_self_management: boolean
        :param allow_self_management: Whether users can specify their own SSH
            public key through the My Settings page. For more information, see
            `Setting an IAM User's Public SSH Key`_.

        """
        params = {'IamUserArn': iam_user_arn, }
        if ssh_username is not None:
            params['SshUsername'] = ssh_username
        if ssh_public_key is not None:
            params['SshPublicKey'] = ssh_public_key
        if allow_self_management is not None:
            params['AllowSelfManagement'] = allow_self_management
        return self.make_request(action='CreateUserProfile',
                                 body=json.dumps(params))

    def delete_app(self, app_id):
        """
        Deletes a specified app.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type app_id: string
        :param app_id: The app ID.

        """
        params = {'AppId': app_id, }
        return self.make_request(action='DeleteApp',
                                 body=json.dumps(params))

    def delete_instance(self, instance_id, delete_elastic_ip=None,
                        delete_volumes=None):
        """
        Deletes a specified instance, which terminates the associated
        Amazon EC2 instance. You must stop an instance before you can
        delete it.

        For more information, see `Deleting Instances`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        :type delete_elastic_ip: boolean
        :param delete_elastic_ip: Whether to delete the instance Elastic IP
            address.

        :type delete_volumes: boolean
        :param delete_volumes: Whether to delete the instance's Amazon EBS
            volumes.

        """
        params = {'InstanceId': instance_id, }
        if delete_elastic_ip is not None:
            params['DeleteElasticIp'] = delete_elastic_ip
        if delete_volumes is not None:
            params['DeleteVolumes'] = delete_volumes
        return self.make_request(action='DeleteInstance',
                                 body=json.dumps(params))

    def delete_layer(self, layer_id):
        """
        Deletes a specified layer. You must first stop and then delete
        all associated instances or unassign registered instances. For
        more information, see `How to Delete a Layer`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type layer_id: string
        :param layer_id: The layer ID.

        """
        params = {'LayerId': layer_id, }
        return self.make_request(action='DeleteLayer',
                                 body=json.dumps(params))

    def delete_stack(self, stack_id):
        """
        Deletes a specified stack. You must first delete all
        instances, layers, and apps or deregister registered
        instances. For more information, see `Shut Down a Stack`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'StackId': stack_id, }
        return self.make_request(action='DeleteStack',
                                 body=json.dumps(params))

    def delete_user_profile(self, iam_user_arn):
        """
        Deletes a user profile.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type iam_user_arn: string
        :param iam_user_arn: The user's IAM ARN.

        """
        params = {'IamUserArn': iam_user_arn, }
        return self.make_request(action='DeleteUserProfile',
                                 body=json.dumps(params))

    def deregister_elastic_ip(self, elastic_ip):
        """
        Deregisters a specified Elastic IP address. The address can
        then be registered by another stack. For more information, see
        `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_ip: string
        :param elastic_ip: The Elastic IP address.

        """
        params = {'ElasticIp': elastic_ip, }
        return self.make_request(action='DeregisterElasticIp',
                                 body=json.dumps(params))

    def deregister_instance(self, instance_id):
        """
        Deregister a registered Amazon EC2 or on-premises instance.
        This action removes the instance from the stack and returns it
        to your control. This action can not be used with instances
        that were created with AWS OpsWorks.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'InstanceId': instance_id, }
        return self.make_request(action='DeregisterInstance',
                                 body=json.dumps(params))

    def deregister_rds_db_instance(self, rds_db_instance_arn):
        """
        Deregisters an Amazon RDS instance.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type rds_db_instance_arn: string
        :param rds_db_instance_arn: The Amazon RDS instance's ARN.

        """
        params = {'RdsDbInstanceArn': rds_db_instance_arn, }
        return self.make_request(action='DeregisterRdsDbInstance',
                                 body=json.dumps(params))

    def deregister_volume(self, volume_id):
        """
        Deregisters an Amazon EBS volume. The volume can then be
        registered by another stack. For more information, see
        `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type volume_id: string
        :param volume_id: The volume ID.

        """
        params = {'VolumeId': volume_id, }
        return self.make_request(action='DeregisterVolume',
                                 body=json.dumps(params))

    def describe_apps(self, stack_id=None, app_ids=None):
        """
        Requests a description of a specified set of apps.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The app stack ID. If you use this parameter,
            `DescribeApps` returns a description of the apps in the specified
            stack.

        :type app_ids: list
        :param app_ids: An array of app IDs for the apps to be described. If
            you use this parameter, `DescribeApps` returns a description of the
            specified apps. Otherwise, it returns a description of every app.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if app_ids is not None:
            params['AppIds'] = app_ids
        return self.make_request(action='DescribeApps',
                                 body=json.dumps(params))

    def describe_commands(self, deployment_id=None, instance_id=None,
                          command_ids=None):
        """
        Describes the results of specified commands.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type deployment_id: string
        :param deployment_id: The deployment ID. If you include this parameter,
            `DescribeCommands` returns a description of the commands associated
            with the specified deployment.

        :type instance_id: string
        :param instance_id: The instance ID. If you include this parameter,
            `DescribeCommands` returns a description of the commands associated
            with the specified instance.

        :type command_ids: list
        :param command_ids: An array of command IDs. If you include this
            parameter, `DescribeCommands` returns a description of the
            specified commands. Otherwise, it returns a description of every
            command.

        """
        params = {}
        if deployment_id is not None:
            params['DeploymentId'] = deployment_id
        if instance_id is not None:
            params['InstanceId'] = instance_id
        if command_ids is not None:
            params['CommandIds'] = command_ids
        return self.make_request(action='DescribeCommands',
                                 body=json.dumps(params))

    def describe_deployments(self, stack_id=None, app_id=None,
                             deployment_ids=None):
        """
        Requests a description of a specified set of deployments.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID. If you include this parameter,
            `DescribeDeployments` returns a description of the commands
            associated with the specified stack.

        :type app_id: string
        :param app_id: The app ID. If you include this parameter,
            `DescribeDeployments` returns a description of the commands
            associated with the specified app.

        :type deployment_ids: list
        :param deployment_ids: An array of deployment IDs to be described. If
            you include this parameter, `DescribeDeployments` returns a
            description of the specified deployments. Otherwise, it returns a
            description of every deployment.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if app_id is not None:
            params['AppId'] = app_id
        if deployment_ids is not None:
            params['DeploymentIds'] = deployment_ids
        return self.make_request(action='DescribeDeployments',
                                 body=json.dumps(params))

    def describe_elastic_ips(self, instance_id=None, stack_id=None, ips=None):
        """
        Describes `Elastic IP addresses`_.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID. If you include this parameter,
            `DescribeElasticIps` returns a description of the Elastic IP
            addresses associated with the specified instance.

        :type stack_id: string
        :param stack_id: A stack ID. If you include this parameter,
            `DescribeElasticIps` returns a description of the Elastic IP
            addresses that are registered with the specified stack.

        :type ips: list
        :param ips: An array of Elastic IP addresses to be described. If you
            include this parameter, `DescribeElasticIps` returns a description
            of the specified Elastic IP addresses. Otherwise, it returns a
            description of every Elastic IP address.

        """
        params = {}
        if instance_id is not None:
            params['InstanceId'] = instance_id
        if stack_id is not None:
            params['StackId'] = stack_id
        if ips is not None:
            params['Ips'] = ips
        return self.make_request(action='DescribeElasticIps',
                                 body=json.dumps(params))

    def describe_elastic_load_balancers(self, stack_id=None, layer_ids=None):
        """
        Describes a stack's Elastic Load Balancing instances.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: A stack ID. The action describes the stack's Elastic
            Load Balancing instances.

        :type layer_ids: list
        :param layer_ids: A list of layer IDs. The action describes the Elastic
            Load Balancing instances for the specified layers.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if layer_ids is not None:
            params['LayerIds'] = layer_ids
        return self.make_request(action='DescribeElasticLoadBalancers',
                                 body=json.dumps(params))

    def describe_instances(self, stack_id=None, layer_id=None,
                           instance_ids=None):
        """
        Requests a description of a set of instances.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: A stack ID. If you use this parameter,
            `DescribeInstances` returns descriptions of the instances
            associated with the specified stack.

        :type layer_id: string
        :param layer_id: A layer ID. If you use this parameter,
            `DescribeInstances` returns descriptions of the instances
            associated with the specified layer.

        :type instance_ids: list
        :param instance_ids: An array of instance IDs to be described. If you
            use this parameter, `DescribeInstances` returns a description of
            the specified instances. Otherwise, it returns a description of
            every instance.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if layer_id is not None:
            params['LayerId'] = layer_id
        if instance_ids is not None:
            params['InstanceIds'] = instance_ids
        return self.make_request(action='DescribeInstances',
                                 body=json.dumps(params))

    def describe_layers(self, stack_id=None, layer_ids=None):
        """
        Requests a description of one or more layers in a specified
        stack.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type layer_ids: list
        :param layer_ids: An array of layer IDs that specify the layers to be
            described. If you omit this parameter, `DescribeLayers` returns a
            description of every layer in the specified stack.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if layer_ids is not None:
            params['LayerIds'] = layer_ids
        return self.make_request(action='DescribeLayers',
                                 body=json.dumps(params))

    def describe_load_based_auto_scaling(self, layer_ids):
        """
        Describes load-based auto scaling configurations for specified
        layers.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type layer_ids: list
        :param layer_ids: An array of layer IDs.

        """
        params = {'LayerIds': layer_ids, }
        return self.make_request(action='DescribeLoadBasedAutoScaling',
                                 body=json.dumps(params))

    def describe_my_user_profile(self):
        """
        Describes a user's SSH information.

        **Required Permissions**: To use this action, an IAM user must
        have self-management enabled or an attached policy that
        explicitly grants permissions. For more information on user
        permissions, see `Managing User Permissions`_.

        
        """
        params = {}
        return self.make_request(action='DescribeMyUserProfile',
                                 body=json.dumps(params))

    def describe_permissions(self, iam_user_arn=None, stack_id=None):
        """
        Describes the permissions for a specified stack.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type iam_user_arn: string
        :param iam_user_arn: The user's IAM ARN. For more information about IAM
            ARNs, see `Using Identifiers`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {}
        if iam_user_arn is not None:
            params['IamUserArn'] = iam_user_arn
        if stack_id is not None:
            params['StackId'] = stack_id
        return self.make_request(action='DescribePermissions',
                                 body=json.dumps(params))

    def describe_raid_arrays(self, instance_id=None, stack_id=None,
                             raid_array_ids=None):
        """
        Describe an instance's RAID arrays.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID. If you use this parameter,
            `DescribeRaidArrays` returns descriptions of the RAID arrays
            associated with the specified instance.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type raid_array_ids: list
        :param raid_array_ids: An array of RAID array IDs. If you use this
            parameter, `DescribeRaidArrays` returns descriptions of the
            specified arrays. Otherwise, it returns a description of every
            array.

        """
        params = {}
        if instance_id is not None:
            params['InstanceId'] = instance_id
        if stack_id is not None:
            params['StackId'] = stack_id
        if raid_array_ids is not None:
            params['RaidArrayIds'] = raid_array_ids
        return self.make_request(action='DescribeRaidArrays',
                                 body=json.dumps(params))

    def describe_rds_db_instances(self, stack_id, rds_db_instance_arns=None):
        """
        Describes Amazon RDS instances.

        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID that the instances are registered with.
            The operation returns descriptions of all registered Amazon RDS
            instances.

        :type rds_db_instance_arns: list
        :param rds_db_instance_arns: An array containing the ARNs of the
            instances to be described.

        """
        params = {'StackId': stack_id, }
        if rds_db_instance_arns is not None:
            params['RdsDbInstanceArns'] = rds_db_instance_arns
        return self.make_request(action='DescribeRdsDbInstances',
                                 body=json.dumps(params))

    def describe_service_errors(self, stack_id=None, instance_id=None,
                                service_error_ids=None):
        """
        Describes AWS OpsWorks service errors.

        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID. If you use this parameter,
            `DescribeServiceErrors` returns descriptions of the errors
            associated with the specified stack.

        :type instance_id: string
        :param instance_id: The instance ID. If you use this parameter,
            `DescribeServiceErrors` returns descriptions of the errors
            associated with the specified instance.

        :type service_error_ids: list
        :param service_error_ids: An array of service error IDs. If you use
            this parameter, `DescribeServiceErrors` returns descriptions of the
            specified errors. Otherwise, it returns a description of every
            error.

        """
        params = {}
        if stack_id is not None:
            params['StackId'] = stack_id
        if instance_id is not None:
            params['InstanceId'] = instance_id
        if service_error_ids is not None:
            params['ServiceErrorIds'] = service_error_ids
        return self.make_request(action='DescribeServiceErrors',
                                 body=json.dumps(params))

    def describe_stack_provisioning_parameters(self, stack_id):
        """
        Requests a description of a stack's provisioning parameters.

        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the stack
        or an attached policy that explicitly grants permissions. For
        more information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID

        """
        params = {'StackId': stack_id, }
        return self.make_request(action='DescribeStackProvisioningParameters',
                                 body=json.dumps(params))

    def describe_stack_summary(self, stack_id):
        """
        Describes the number of layers and apps in a specified stack,
        and the number of instances in each state, such as
        `running_setup` or `online`.

        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'StackId': stack_id, }
        return self.make_request(action='DescribeStackSummary',
                                 body=json.dumps(params))

    def describe_stacks(self, stack_ids=None):
        """
        Requests a description of one or more stacks.

        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type stack_ids: list
        :param stack_ids: An array of stack IDs that specify the stacks to be
            described. If you omit this parameter, `DescribeStacks` returns a
            description of every stack.

        """
        params = {}
        if stack_ids is not None:
            params['StackIds'] = stack_ids
        return self.make_request(action='DescribeStacks',
                                 body=json.dumps(params))

    def describe_time_based_auto_scaling(self, instance_ids):
        """
        Describes time-based auto scaling configurations for specified
        instances.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type instance_ids: list
        :param instance_ids: An array of instance IDs.

        """
        params = {'InstanceIds': instance_ids, }
        return self.make_request(action='DescribeTimeBasedAutoScaling',
                                 body=json.dumps(params))

    def describe_user_profiles(self, iam_user_arns=None):
        """
        Describe specified users.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type iam_user_arns: list
        :param iam_user_arns: An array of IAM user ARNs that identify the users
            to be described.

        """
        params = {}
        if iam_user_arns is not None:
            params['IamUserArns'] = iam_user_arns
        return self.make_request(action='DescribeUserProfiles',
                                 body=json.dumps(params))

    def describe_volumes(self, instance_id=None, stack_id=None,
                         raid_array_id=None, volume_ids=None):
        """
        Describes an instance's Amazon EBS volumes.


        You must specify at least one of the parameters.


        **Required Permissions**: To use this action, an IAM user must
        have a Show, Deploy, or Manage permissions level for the
        stack, or an attached policy that explicitly grants
        permissions. For more information on user permissions, see
        `Managing User Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID. If you use this parameter,
            `DescribeVolumes` returns descriptions of the volumes associated
            with the specified instance.

        :type stack_id: string
        :param stack_id: A stack ID. The action describes the stack's
            registered Amazon EBS volumes.

        :type raid_array_id: string
        :param raid_array_id: The RAID array ID. If you use this parameter,
            `DescribeVolumes` returns descriptions of the volumes associated
            with the specified RAID array.

        :type volume_ids: list
        :param volume_ids: Am array of volume IDs. If you use this parameter,
            `DescribeVolumes` returns descriptions of the specified volumes.
            Otherwise, it returns a description of every volume.

        """
        params = {}
        if instance_id is not None:
            params['InstanceId'] = instance_id
        if stack_id is not None:
            params['StackId'] = stack_id
        if raid_array_id is not None:
            params['RaidArrayId'] = raid_array_id
        if volume_ids is not None:
            params['VolumeIds'] = volume_ids
        return self.make_request(action='DescribeVolumes',
                                 body=json.dumps(params))

    def detach_elastic_load_balancer(self, elastic_load_balancer_name,
                                     layer_id):
        """
        Detaches a specified Elastic Load Balancing instance from its
        layer.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_load_balancer_name: string
        :param elastic_load_balancer_name: The Elastic Load Balancing
            instance's name.

        :type layer_id: string
        :param layer_id: The ID of the layer that the Elastic Load Balancing
            instance is attached to.

        """
        params = {
            'ElasticLoadBalancerName': elastic_load_balancer_name,
            'LayerId': layer_id,
        }
        return self.make_request(action='DetachElasticLoadBalancer',
                                 body=json.dumps(params))

    def disassociate_elastic_ip(self, elastic_ip):
        """
        Disassociates an Elastic IP address from its instance. The
        address remains registered with the stack. For more
        information, see `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_ip: string
        :param elastic_ip: The Elastic IP address.

        """
        params = {'ElasticIp': elastic_ip, }
        return self.make_request(action='DisassociateElasticIp',
                                 body=json.dumps(params))

    def get_hostname_suggestion(self, layer_id):
        """
        Gets a generated host name for the specified layer, based on
        the current host name theme.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type layer_id: string
        :param layer_id: The layer ID.

        """
        params = {'LayerId': layer_id, }
        return self.make_request(action='GetHostnameSuggestion',
                                 body=json.dumps(params))

    def reboot_instance(self, instance_id):
        """
        Reboots a specified instance. For more information, see
        `Starting, Stopping, and Rebooting Instances`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'InstanceId': instance_id, }
        return self.make_request(action='RebootInstance',
                                 body=json.dumps(params))

    def register_elastic_ip(self, elastic_ip, stack_id):
        """
        Registers an Elastic IP address with a specified stack. An
        address can be registered with only one stack at a time. If
        the address is already registered, you must first deregister
        it by calling DeregisterElasticIp. For more information, see
        `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_ip: string
        :param elastic_ip: The Elastic IP address.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'ElasticIp': elastic_ip, 'StackId': stack_id, }
        return self.make_request(action='RegisterElasticIp',
                                 body=json.dumps(params))

    def register_instance(self, stack_id, hostname=None, public_ip=None,
                          private_ip=None, rsa_public_key=None,
                          rsa_public_key_fingerprint=None,
                          instance_identity=None):
        """
        Registers instances with a specified stack that were created
        outside of AWS OpsWorks.

        We do not recommend using this action to register instances.
        The complete registration operation has two primary steps,
        installing the AWS OpsWorks agent on the instance and
        registering the instance with the stack. `RegisterInstance`
        handles only the second step. You should instead use the AWS
        CLI `register` command, which performs the entire registration
        operation.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The ID of the stack that the instance is to be
            registered with.

        :type hostname: string
        :param hostname: The instance's hostname.

        :type public_ip: string
        :param public_ip: The instance's public IP address.

        :type private_ip: string
        :param private_ip: The instance's private IP address.

        :type rsa_public_key: string
        :param rsa_public_key: The instances public RSA key. This key is used
            to encrypt communication between the instance and the service.

        :type rsa_public_key_fingerprint: string
        :param rsa_public_key_fingerprint: The instances public RSA key
            fingerprint.

        :type instance_identity: dict
        :param instance_identity: An InstanceIdentity object that contains the
            instance's identity.

        """
        params = {'StackId': stack_id, }
        if hostname is not None:
            params['Hostname'] = hostname
        if public_ip is not None:
            params['PublicIp'] = public_ip
        if private_ip is not None:
            params['PrivateIp'] = private_ip
        if rsa_public_key is not None:
            params['RsaPublicKey'] = rsa_public_key
        if rsa_public_key_fingerprint is not None:
            params['RsaPublicKeyFingerprint'] = rsa_public_key_fingerprint
        if instance_identity is not None:
            params['InstanceIdentity'] = instance_identity
        return self.make_request(action='RegisterInstance',
                                 body=json.dumps(params))

    def register_rds_db_instance(self, stack_id, rds_db_instance_arn,
                                 db_user, db_password):
        """
        Registers an Amazon RDS instance with a stack.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type rds_db_instance_arn: string
        :param rds_db_instance_arn: The Amazon RDS instance's ARN.

        :type db_user: string
        :param db_user: The database's master user name.

        :type db_password: string
        :param db_password: The database password.

        """
        params = {
            'StackId': stack_id,
            'RdsDbInstanceArn': rds_db_instance_arn,
            'DbUser': db_user,
            'DbPassword': db_password,
        }
        return self.make_request(action='RegisterRdsDbInstance',
                                 body=json.dumps(params))

    def register_volume(self, stack_id, ec_2_volume_id=None):
        """
        Registers an Amazon EBS volume with a specified stack. A
        volume can be registered with only one stack at a time. If the
        volume is already registered, you must first deregister it by
        calling DeregisterVolume. For more information, see `Resource
        Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type ec_2_volume_id: string
        :param ec_2_volume_id: The Amazon EBS volume ID.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'StackId': stack_id, }
        if ec_2_volume_id is not None:
            params['Ec2VolumeId'] = ec_2_volume_id
        return self.make_request(action='RegisterVolume',
                                 body=json.dumps(params))

    def set_load_based_auto_scaling(self, layer_id, enable=None,
                                    up_scaling=None, down_scaling=None):
        """
        Specify the load-based auto scaling configuration for a
        specified layer. For more information, see `Managing Load with
        Time-based and Load-based Instances`_.


        To use load-based auto scaling, you must create a set of load-
        based auto scaling instances. Load-based auto scaling operates
        only on the instances from that set, so you must ensure that
        you have created enough instances to handle the maximum
        anticipated load.


        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type layer_id: string
        :param layer_id: The layer ID.

        :type enable: boolean
        :param enable: Enables load-based auto scaling for the layer.

        :type up_scaling: dict
        :param up_scaling: An `AutoScalingThresholds` object with the upscaling
            threshold configuration. If the load exceeds these thresholds for a
            specified amount of time, AWS OpsWorks starts a specified number of
            instances.

        :type down_scaling: dict
        :param down_scaling: An `AutoScalingThresholds` object with the
            downscaling threshold configuration. If the load falls below these
            thresholds for a specified amount of time, AWS OpsWorks stops a
            specified number of instances.

        """
        params = {'LayerId': layer_id, }
        if enable is not None:
            params['Enable'] = enable
        if up_scaling is not None:
            params['UpScaling'] = up_scaling
        if down_scaling is not None:
            params['DownScaling'] = down_scaling
        return self.make_request(action='SetLoadBasedAutoScaling',
                                 body=json.dumps(params))

    def set_permission(self, stack_id, iam_user_arn, allow_ssh=None,
                       allow_sudo=None, level=None):
        """
        Specifies a user's permissions. For more information, see
        `Security and Permissions`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type iam_user_arn: string
        :param iam_user_arn: The user's IAM ARN.

        :type allow_ssh: boolean
        :param allow_ssh: The user is allowed to use SSH to communicate with
            the instance.

        :type allow_sudo: boolean
        :param allow_sudo: The user is allowed to use **sudo** to elevate
            privileges.

        :type level: string
        :param level: The user's permission level, which must be set to one of
            the following strings. You cannot set your own permissions level.

        + `deny`
        + `show`
        + `deploy`
        + `manage`
        + `iam_only`


        For more information on the permissions associated with these levels,
            see `Managing User Permissions`_

        """
        params = {'StackId': stack_id, 'IamUserArn': iam_user_arn, }
        if allow_ssh is not None:
            params['AllowSsh'] = allow_ssh
        if allow_sudo is not None:
            params['AllowSudo'] = allow_sudo
        if level is not None:
            params['Level'] = level
        return self.make_request(action='SetPermission',
                                 body=json.dumps(params))

    def set_time_based_auto_scaling(self, instance_id,
                                    auto_scaling_schedule=None):
        """
        Specify the time-based auto scaling configuration for a
        specified instance. For more information, see `Managing Load
        with Time-based and Load-based Instances`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        :type auto_scaling_schedule: dict
        :param auto_scaling_schedule: An `AutoScalingSchedule` with the
            instance schedule.

        """
        params = {'InstanceId': instance_id, }
        if auto_scaling_schedule is not None:
            params['AutoScalingSchedule'] = auto_scaling_schedule
        return self.make_request(action='SetTimeBasedAutoScaling',
                                 body=json.dumps(params))

    def start_instance(self, instance_id):
        """
        Starts a specified instance. For more information, see
        `Starting, Stopping, and Rebooting Instances`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'InstanceId': instance_id, }
        return self.make_request(action='StartInstance',
                                 body=json.dumps(params))

    def start_stack(self, stack_id):
        """
        Starts a stack's instances.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'StackId': stack_id, }
        return self.make_request(action='StartStack',
                                 body=json.dumps(params))

    def stop_instance(self, instance_id):
        """
        Stops a specified instance. When you stop a standard instance,
        the data disappears and must be reinstalled when you restart
        the instance. You can stop an Amazon EBS-backed instance
        without losing data. For more information, see `Starting,
        Stopping, and Rebooting Instances`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'InstanceId': instance_id, }
        return self.make_request(action='StopInstance',
                                 body=json.dumps(params))

    def stop_stack(self, stack_id):
        """
        Stops a specified stack.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        """
        params = {'StackId': stack_id, }
        return self.make_request(action='StopStack',
                                 body=json.dumps(params))

    def unassign_instance(self, instance_id):
        """
        Unassigns a registered instance from all of it's layers. The
        instance remains in the stack as an unassigned instance and
        can be assigned to another layer, as needed. You cannot use
        this action with instances that were created with AWS
        OpsWorks.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        """
        params = {'InstanceId': instance_id, }
        return self.make_request(action='UnassignInstance',
                                 body=json.dumps(params))

    def unassign_volume(self, volume_id):
        """
        Unassigns an assigned Amazon EBS volume. The volume remains
        registered with the stack. For more information, see `Resource
        Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type volume_id: string
        :param volume_id: The volume ID.

        """
        params = {'VolumeId': volume_id, }
        return self.make_request(action='UnassignVolume',
                                 body=json.dumps(params))

    def update_app(self, app_id, name=None, description=None,
                   data_sources=None, type=None, app_source=None,
                   domains=None, enable_ssl=None, ssl_configuration=None,
                   attributes=None, environment=None):
        """
        Updates a specified app.

        **Required Permissions**: To use this action, an IAM user must
        have a Deploy or Manage permissions level for the stack, or an
        attached policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type app_id: string
        :param app_id: The app ID.

        :type name: string
        :param name: The app name.

        :type description: string
        :param description: A description of the app.

        :type data_sources: list
        :param data_sources: The app's data sources.

        :type type: string
        :param type: The app type.

        :type app_source: dict
        :param app_source: A `Source` object that specifies the app repository.

        :type domains: list
        :param domains: The app's virtual host settings, with multiple domains
            separated by commas. For example: `'www.example.com, example.com'`

        :type enable_ssl: boolean
        :param enable_ssl: Whether SSL is enabled for the app.

        :type ssl_configuration: dict
        :param ssl_configuration: An `SslConfiguration` object with the SSL
            configuration.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type environment: list
        :param environment:
        An array of `EnvironmentVariable` objects that specify environment
            variables to be associated with the app. You can specify up to ten
            environment variables. After you deploy the app, these variables
            are defined on the associated app server instances.

        This parameter is supported only by Chef 11.10 stacks. If you have
            specified one or more environment variables, you cannot modify the
            stack's Chef version.

        """
        params = {'AppId': app_id, }
        if name is not None:
            params['Name'] = name
        if description is not None:
            params['Description'] = description
        if data_sources is not None:
            params['DataSources'] = data_sources
        if type is not None:
            params['Type'] = type
        if app_source is not None:
            params['AppSource'] = app_source
        if domains is not None:
            params['Domains'] = domains
        if enable_ssl is not None:
            params['EnableSsl'] = enable_ssl
        if ssl_configuration is not None:
            params['SslConfiguration'] = ssl_configuration
        if attributes is not None:
            params['Attributes'] = attributes
        if environment is not None:
            params['Environment'] = environment
        return self.make_request(action='UpdateApp',
                                 body=json.dumps(params))

    def update_elastic_ip(self, elastic_ip, name=None):
        """
        Updates a registered Elastic IP address's name. For more
        information, see `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type elastic_ip: string
        :param elastic_ip: The address.

        :type name: string
        :param name: The new name.

        """
        params = {'ElasticIp': elastic_ip, }
        if name is not None:
            params['Name'] = name
        return self.make_request(action='UpdateElasticIp',
                                 body=json.dumps(params))

    def update_instance(self, instance_id, layer_ids=None,
                        instance_type=None, auto_scaling_type=None,
                        hostname=None, os=None, ami_id=None,
                        ssh_key_name=None, architecture=None,
                        install_updates_on_boot=None, ebs_optimized=None):
        """
        Updates a specified instance.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type instance_id: string
        :param instance_id: The instance ID.

        :type layer_ids: list
        :param layer_ids: The instance's layer IDs.

        :type instance_type: string
        :param instance_type: The instance type. AWS OpsWorks supports all
            instance types except Cluster Compute, Cluster GPU, and High Memory
            Cluster. For more information, see `Instance Families and Types`_.
            The parameter values that you use to specify the various types are
            in the API Name column of the Available Instance Types table.

        :type auto_scaling_type: string
        :param auto_scaling_type: For load-based or time-based instances, the
            type.

        :type hostname: string
        :param hostname: The instance host name.

        :type os: string
        :param os: The instance's operating system, which must be set to one of
            the following.

        + Standard operating systems: An Amazon Linux version such as `Amazon
              Linux 2014.09`, `Ubuntu 12.04 LTS`, or `Ubuntu 14.04 LTS`.
        + Custom AMIs: `Custom`


        The default option is the current Amazon Linux version, such as `Amazon
            Linux 2014.09`. If you set this parameter to `Custom`, you must use
            the CreateInstance action's AmiId parameter to specify the custom
            AMI that you want to use. For more information on the standard
            operating systems, see `Operating Systems`_For more information on
            how to use custom AMIs with OpsWorks, see `Using Custom AMIs`_.

        :type ami_id: string
        :param ami_id:
        A custom AMI ID to be used to create the instance. The AMI should be
            based on one of the standard AWS OpsWorks AMIs: Amazon Linux,
            Ubuntu 12.04 LTS, or Ubuntu 14.04 LTS. For more information, see
            `Instances`_

        If you specify a custom AMI, you must set `Os` to `Custom`.

        :type ssh_key_name: string
        :param ssh_key_name: The instance SSH key name.

        :type architecture: string
        :param architecture: The instance architecture. Instance types do not
            necessarily support both architectures. For a list of the
            architectures that are supported by the different instance types,
            see `Instance Families and Types`_.

        :type install_updates_on_boot: boolean
        :param install_updates_on_boot:
        Whether to install operating system and package updates when the
            instance boots. The default value is `True`. To control when
            updates are installed, set this value to `False`. You must then
            update your instances manually by using CreateDeployment to run the
            `update_dependencies` stack command or manually running `yum`
            (Amazon Linux) or `apt-get` (Ubuntu) on the instances.


        We strongly recommend using the default value of `True`, to ensure that
            your instances have the latest security updates.

        :type ebs_optimized: boolean
        :param ebs_optimized: Whether this is an Amazon EBS-optimized instance.

        """
        params = {'InstanceId': instance_id, }
        if layer_ids is not None:
            params['LayerIds'] = layer_ids
        if instance_type is not None:
            params['InstanceType'] = instance_type
        if auto_scaling_type is not None:
            params['AutoScalingType'] = auto_scaling_type
        if hostname is not None:
            params['Hostname'] = hostname
        if os is not None:
            params['Os'] = os
        if ami_id is not None:
            params['AmiId'] = ami_id
        if ssh_key_name is not None:
            params['SshKeyName'] = ssh_key_name
        if architecture is not None:
            params['Architecture'] = architecture
        if install_updates_on_boot is not None:
            params['InstallUpdatesOnBoot'] = install_updates_on_boot
        if ebs_optimized is not None:
            params['EbsOptimized'] = ebs_optimized
        return self.make_request(action='UpdateInstance',
                                 body=json.dumps(params))

    def update_layer(self, layer_id, name=None, shortname=None,
                     attributes=None, custom_instance_profile_arn=None,
                     custom_security_group_ids=None, packages=None,
                     volume_configurations=None, enable_auto_healing=None,
                     auto_assign_elastic_ips=None,
                     auto_assign_public_ips=None, custom_recipes=None,
                     install_updates_on_boot=None,
                     use_ebs_optimized_instances=None,
                     lifecycle_event_configuration=None):
        """
        Updates a specified layer.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type layer_id: string
        :param layer_id: The layer ID.

        :type name: string
        :param name: The layer name, which is used by the console.

        :type shortname: string
        :param shortname: The layer short name, which is used internally by AWS
            OpsWorksand by Chef. The short name is also used as the name for
            the directory where your app files are installed. It can have a
            maximum of 200 characters and must be in the following format:
            /\A[a-z0-9\-\_\.]+\Z/.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type custom_instance_profile_arn: string
        :param custom_instance_profile_arn: The ARN of an IAM profile to be
            used for all of the layer's EC2 instances. For more information
            about IAM ARNs, see `Using Identifiers`_.

        :type custom_security_group_ids: list
        :param custom_security_group_ids: An array containing the layer's
            custom security group IDs.

        :type packages: list
        :param packages: An array of `Package` objects that describe the
            layer's packages.

        :type volume_configurations: list
        :param volume_configurations: A `VolumeConfigurations` object that
            describes the layer's Amazon EBS volumes.

        :type enable_auto_healing: boolean
        :param enable_auto_healing: Whether to disable auto healing for the
            layer.

        :type auto_assign_elastic_ips: boolean
        :param auto_assign_elastic_ips: Whether to automatically assign an
            `Elastic IP address`_ to the layer's instances. For more
            information, see `How to Edit a Layer`_.

        :type auto_assign_public_ips: boolean
        :param auto_assign_public_ips: For stacks that are running in a VPC,
            whether to automatically assign a public IP address to the layer's
            instances. For more information, see `How to Edit a Layer`_.

        :type custom_recipes: dict
        :param custom_recipes: A `LayerCustomRecipes` object that specifies the
            layer's custom recipes.

        :type install_updates_on_boot: boolean
        :param install_updates_on_boot:
        Whether to install operating system and package updates when the
            instance boots. The default value is `True`. To control when
            updates are installed, set this value to `False`. You must then
            update your instances manually by using CreateDeployment to run the
            `update_dependencies` stack command or manually running `yum`
            (Amazon Linux) or `apt-get` (Ubuntu) on the instances.


        We strongly recommend using the default value of `True`, to ensure that
            your instances have the latest security updates.

        :type use_ebs_optimized_instances: boolean
        :param use_ebs_optimized_instances: Whether to use Amazon EBS-optimized
            instances.

        :type lifecycle_event_configuration: dict
        :param lifecycle_event_configuration:

        """
        params = {'LayerId': layer_id, }
        if name is not None:
            params['Name'] = name
        if shortname is not None:
            params['Shortname'] = shortname
        if attributes is not None:
            params['Attributes'] = attributes
        if custom_instance_profile_arn is not None:
            params['CustomInstanceProfileArn'] = custom_instance_profile_arn
        if custom_security_group_ids is not None:
            params['CustomSecurityGroupIds'] = custom_security_group_ids
        if packages is not None:
            params['Packages'] = packages
        if volume_configurations is not None:
            params['VolumeConfigurations'] = volume_configurations
        if enable_auto_healing is not None:
            params['EnableAutoHealing'] = enable_auto_healing
        if auto_assign_elastic_ips is not None:
            params['AutoAssignElasticIps'] = auto_assign_elastic_ips
        if auto_assign_public_ips is not None:
            params['AutoAssignPublicIps'] = auto_assign_public_ips
        if custom_recipes is not None:
            params['CustomRecipes'] = custom_recipes
        if install_updates_on_boot is not None:
            params['InstallUpdatesOnBoot'] = install_updates_on_boot
        if use_ebs_optimized_instances is not None:
            params['UseEbsOptimizedInstances'] = use_ebs_optimized_instances
        if lifecycle_event_configuration is not None:
            params['LifecycleEventConfiguration'] = lifecycle_event_configuration
        return self.make_request(action='UpdateLayer',
                                 body=json.dumps(params))

    def update_my_user_profile(self, ssh_public_key=None):
        """
        Updates a user's SSH public key.

        **Required Permissions**: To use this action, an IAM user must
        have self-management enabled or an attached policy that
        explicitly grants permissions. For more information on user
        permissions, see `Managing User Permissions`_.

        :type ssh_public_key: string
        :param ssh_public_key: The user's SSH public key.

        """
        params = {}
        if ssh_public_key is not None:
            params['SshPublicKey'] = ssh_public_key
        return self.make_request(action='UpdateMyUserProfile',
                                 body=json.dumps(params))

    def update_rds_db_instance(self, rds_db_instance_arn, db_user=None,
                               db_password=None):
        """
        Updates an Amazon RDS instance.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type rds_db_instance_arn: string
        :param rds_db_instance_arn: The Amazon RDS instance's ARN.

        :type db_user: string
        :param db_user: The master user name.

        :type db_password: string
        :param db_password: The database password.

        """
        params = {'RdsDbInstanceArn': rds_db_instance_arn, }
        if db_user is not None:
            params['DbUser'] = db_user
        if db_password is not None:
            params['DbPassword'] = db_password
        return self.make_request(action='UpdateRdsDbInstance',
                                 body=json.dumps(params))

    def update_stack(self, stack_id, name=None, attributes=None,
                     service_role_arn=None,
                     default_instance_profile_arn=None, default_os=None,
                     hostname_theme=None, default_availability_zone=None,
                     default_subnet_id=None, custom_json=None,
                     configuration_manager=None, chef_configuration=None,
                     use_custom_cookbooks=None, custom_cookbooks_source=None,
                     default_ssh_key_name=None,
                     default_root_device_type=None,
                     use_opsworks_security_groups=None):
        """
        Updates a specified stack.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type stack_id: string
        :param stack_id: The stack ID.

        :type name: string
        :param name: The stack's new name.

        :type attributes: map
        :param attributes: One or more user-defined key/value pairs to be added
            to the stack attributes.

        :type service_role_arn: string
        :param service_role_arn:
        The stack AWS Identity and Access Management (IAM) role, which allows
            AWS OpsWorks to work with AWS resources on your behalf. You must
            set this parameter to the Amazon Resource Name (ARN) for an
            existing IAM role. For more information about IAM ARNs, see `Using
            Identifiers`_.


        You must set this parameter to a valid service role ARN or the action
            will fail; there is no default value. You can specify the stack's
            current service role ARN, if you prefer, but you must do so
            explicitly.

        :type default_instance_profile_arn: string
        :param default_instance_profile_arn: The ARN of an IAM profile that is
            the default profile for all of the stack's EC2 instances. For more
            information about IAM ARNs, see `Using Identifiers`_.

        :type default_os: string
        :param default_os: The stack's operating system, which must be set to
            one of the following.

        + Standard operating systems: an Amazon Linux version such as `Amazon
              Linux 2014.09`, `Ubuntu 12.04 LTS`, or `Ubuntu 14.04 LTS`.
        + Custom AMIs: `Custom`. You specify the custom AMI you want to use
              when you create instances.


        The default option is the current Amazon Linux version.

        :type hostname_theme: string
        :param hostname_theme: The stack's new host name theme, with spaces are
            replaced by underscores. The theme is used to generate host names
            for the stack's instances. By default, `HostnameTheme` is set to
            `Layer_Dependent`, which creates host names by appending integers
            to the layer's short name. The other themes are:

        + `Baked_Goods`
        + `Clouds`
        + `European_Cities`
        + `Fruits`
        + `Greek_Deities`
        + `Legendary_Creatures_from_Japan`
        + `Planets_and_Moons`
        + `Roman_Deities`
        + `Scottish_Islands`
        + `US_Cities`
        + `Wild_Cats`


        To obtain a generated host name, call `GetHostNameSuggestion`, which
            returns a host name based on the current theme.

        :type default_availability_zone: string
        :param default_availability_zone: The stack's default Availability
            Zone, which must be in the specified region. For more information,
            see `Regions and Endpoints`_. If you also specify a value for
            `DefaultSubnetId`, the subnet must be in the same zone. For more
            information, see CreateStack.

        :type default_subnet_id: string
        :param default_subnet_id: The stack's default VPC subnet ID. This
            parameter is required if you specify a value for the `VpcId`
            parameter. All instances are launched into this subnet unless you
            specify otherwise when you create the instance. If you also specify
            a value for `DefaultAvailabilityZone`, the subnet must be in that
            zone. For information on default values and when this parameter is
            required, see the `VpcId` parameter description.

        :type custom_json: string
        :param custom_json: A string that contains user-defined, custom JSON.
            It is used to override the corresponding default stack
            configuration JSON values. The string should be in the following
            format and must escape characters such as '"'.:
        `"{\"key1\": \"value1\", \"key2\": \"value2\",...}"`

        For more information on custom JSON, see `Use Custom JSON to Modify the
            Stack Configuration JSON`_.

        :type configuration_manager: dict
        :param configuration_manager: The configuration manager. When you clone
            a stack we recommend that you use the configuration manager to
            specify the Chef version, 0.9, 11.4, or 11.10. The default value is
            currently 11.4.

        :type chef_configuration: dict
        :param chef_configuration: A `ChefConfiguration` object that specifies
            whether to enable Berkshelf and the Berkshelf version on Chef 11.10
            stacks. For more information, see `Create a New Stack`_.

        :type use_custom_cookbooks: boolean
        :param use_custom_cookbooks: Whether the stack uses custom cookbooks.

        :type custom_cookbooks_source: dict
        :param custom_cookbooks_source: Contains the information required to
            retrieve an app or cookbook from a repository. For more
            information, see `Creating Apps`_ or `Custom Recipes and
            Cookbooks`_.

        :type default_ssh_key_name: string
        :param default_ssh_key_name: A default SSH key for the stack instances.
            You can override this value when you create or update an instance.

        :type default_root_device_type: string
        :param default_root_device_type: The default root device type. This
            value is used by default for all instances in the stack, but you
            can override it when you create an instance. For more information,
            see `Storage for the Root Device`_.

        :type use_opsworks_security_groups: boolean
        :param use_opsworks_security_groups: Whether to associate the AWS
            OpsWorks built-in security groups with the stack's layers.
        AWS OpsWorks provides a standard set of built-in security groups, one
            for each layer, which are associated with layers by default.
            `UseOpsworksSecurityGroups` allows you to instead provide your own
            custom security groups. `UseOpsworksSecurityGroups` has the
            following settings:


        + True - AWS OpsWorks automatically associates the appropriate built-in
              security group with each layer (default setting). You can associate
              additional security groups with a layer after you create it but you
              cannot delete the built-in security group.
        + False - AWS OpsWorks does not associate built-in security groups with
              layers. You must create appropriate EC2 security groups and
              associate a security group with each layer that you create.
              However, you can still manually associate a built-in security group
              with a layer on creation; custom security groups are required only
              for those layers that need custom settings.


        For more information, see `Create a New Stack`_.

        """
        params = {'StackId': stack_id, }
        if name is not None:
            params['Name'] = name
        if attributes is not None:
            params['Attributes'] = attributes
        if service_role_arn is not None:
            params['ServiceRoleArn'] = service_role_arn
        if default_instance_profile_arn is not None:
            params['DefaultInstanceProfileArn'] = default_instance_profile_arn
        if default_os is not None:
            params['DefaultOs'] = default_os
        if hostname_theme is not None:
            params['HostnameTheme'] = hostname_theme
        if default_availability_zone is not None:
            params['DefaultAvailabilityZone'] = default_availability_zone
        if default_subnet_id is not None:
            params['DefaultSubnetId'] = default_subnet_id
        if custom_json is not None:
            params['CustomJson'] = custom_json
        if configuration_manager is not None:
            params['ConfigurationManager'] = configuration_manager
        if chef_configuration is not None:
            params['ChefConfiguration'] = chef_configuration
        if use_custom_cookbooks is not None:
            params['UseCustomCookbooks'] = use_custom_cookbooks
        if custom_cookbooks_source is not None:
            params['CustomCookbooksSource'] = custom_cookbooks_source
        if default_ssh_key_name is not None:
            params['DefaultSshKeyName'] = default_ssh_key_name
        if default_root_device_type is not None:
            params['DefaultRootDeviceType'] = default_root_device_type
        if use_opsworks_security_groups is not None:
            params['UseOpsworksSecurityGroups'] = use_opsworks_security_groups
        return self.make_request(action='UpdateStack',
                                 body=json.dumps(params))

    def update_user_profile(self, iam_user_arn, ssh_username=None,
                            ssh_public_key=None, allow_self_management=None):
        """
        Updates a specified user profile.

        **Required Permissions**: To use this action, an IAM user must
        have an attached policy that explicitly grants permissions.
        For more information on user permissions, see `Managing User
        Permissions`_.

        :type iam_user_arn: string
        :param iam_user_arn: The user IAM ARN.

        :type ssh_username: string
        :param ssh_username: The user's SSH user name. The allowable characters
            are [a-z], [A-Z], [0-9], '-', and '_'. If the specified name
            includes other punctuation marks, AWS OpsWorks removes them. For
            example, `my.name` will be changed to `myname`. If you do not
            specify an SSH user name, AWS OpsWorks generates one from the IAM
            user name.

        :type ssh_public_key: string
        :param ssh_public_key: The user's new SSH public key.

        :type allow_self_management: boolean
        :param allow_self_management: Whether users can specify their own SSH
            public key through the My Settings page. For more information, see
            `Managing User Permissions`_.

        """
        params = {'IamUserArn': iam_user_arn, }
        if ssh_username is not None:
            params['SshUsername'] = ssh_username
        if ssh_public_key is not None:
            params['SshPublicKey'] = ssh_public_key
        if allow_self_management is not None:
            params['AllowSelfManagement'] = allow_self_management
        return self.make_request(action='UpdateUserProfile',
                                 body=json.dumps(params))

    def update_volume(self, volume_id, name=None, mount_point=None):
        """
        Updates an Amazon EBS volume's name or mount point. For more
        information, see `Resource Management`_.

        **Required Permissions**: To use this action, an IAM user must
        have a Manage permissions level for the stack, or an attached
        policy that explicitly grants permissions. For more
        information on user permissions, see `Managing User
        Permissions`_.

        :type volume_id: string
        :param volume_id: The volume ID.

        :type name: string
        :param name: The new name.

        :type mount_point: string
        :param mount_point: The new mount point.

        """
        params = {'VolumeId': volume_id, }
        if name is not None:
            params['Name'] = name
        if mount_point is not None:
            params['MountPoint'] = mount_point
        return self.make_request(action='UpdateVolume',
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

