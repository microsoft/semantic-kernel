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
from boto.codedeploy import exceptions


class CodeDeployConnection(AWSQueryConnection):
    """
    AWS CodeDeploy **Overview**
    This is the AWS CodeDeploy API Reference. This guide provides
    descriptions of the AWS CodeDeploy APIs. For additional
    information, see the `AWS CodeDeploy User Guide`_.
    **Using the APIs**
    You can use the AWS CodeDeploy APIs to work with the following
    items:


    + Applications , which are unique identifiers that AWS CodeDeploy
      uses to ensure that the correct combinations of revisions,
      deployment configurations, and deployment groups are being
      referenced during deployments. You can work with applications by
      calling CreateApplication, DeleteApplication, GetApplication,
      ListApplications, BatchGetApplications, and UpdateApplication to
      create, delete, and get information about applications, and to
      change information about an application, respectively.
    + Deployment configurations , which are sets of deployment rules
      and deployment success and failure conditions that AWS CodeDeploy
      uses during deployments. You can work with deployment
      configurations by calling CreateDeploymentConfig,
      DeleteDeploymentConfig, GetDeploymentConfig, and
      ListDeploymentConfigs to create, delete, and get information about
      deployment configurations, respectively.
    + Deployment groups , which represent groups of Amazon EC2
      instances to which application revisions can be deployed. You can
      work with deployment groups by calling CreateDeploymentGroup,
      DeleteDeploymentGroup, GetDeploymentGroup, ListDeploymentGroups,
      and UpdateDeploymentGroup to create, delete, and get information
      about single and multiple deployment groups, and to change
      information about a deployment group, respectively.
    + Deployment instances (also known simply as instances ), which
      represent Amazon EC2 instances to which application revisions are
      deployed. Deployment instances are identified by their Amazon EC2
      tags or Auto Scaling group names. Deployment instances belong to
      deployment groups. You can work with deployment instances by
      calling GetDeploymentInstance and ListDeploymentInstances to get
      information about single and multiple deployment instances,
      respectively.
    + Deployments , which represent the process of deploying revisions
      to deployment groups. You can work with deployments by calling
      CreateDeployment, GetDeployment, ListDeployments,
      BatchGetDeployments, and StopDeployment to create and get
      information about deployments, and to stop a deployment,
      respectively.
    + Application revisions (also known simply as revisions ), which
      are archive files that are stored in Amazon S3 buckets or GitHub
      repositories. These revisions contain source content (such as
      source code, web pages, executable files, any deployment scripts,
      and similar) along with an Application Specification file (AppSpec
      file). (The AppSpec file is unique to AWS CodeDeploy; it defines a
      series of deployment actions that you want AWS CodeDeploy to
      execute.) An application revision is uniquely identified by its
      Amazon S3 object key and its ETag, version, or both. Application
      revisions are deployed to deployment groups. You can work with
      application revisions by calling GetApplicationRevision,
      ListApplicationRevisions, and RegisterApplicationRevision to get
      information about application revisions and to inform AWS
      CodeDeploy about an application revision, respectively.
    """
    APIVersion = "2014-10-06"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "codedeploy.us-east-1.amazonaws.com"
    ServiceName = "codedeploy"
    TargetPrefix = "CodeDeploy_20141006"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidDeploymentIdException": exceptions.InvalidDeploymentIdException,
        "InvalidDeploymentGroupNameException": exceptions.InvalidDeploymentGroupNameException,
        "DeploymentConfigAlreadyExistsException": exceptions.DeploymentConfigAlreadyExistsException,
        "InvalidRoleException": exceptions.InvalidRoleException,
        "RoleRequiredException": exceptions.RoleRequiredException,
        "DeploymentGroupAlreadyExistsException": exceptions.DeploymentGroupAlreadyExistsException,
        "DeploymentConfigLimitExceededException": exceptions.DeploymentConfigLimitExceededException,
        "InvalidNextTokenException": exceptions.InvalidNextTokenException,
        "InvalidDeploymentConfigNameException": exceptions.InvalidDeploymentConfigNameException,
        "InvalidSortByException": exceptions.InvalidSortByException,
        "InstanceDoesNotExistException": exceptions.InstanceDoesNotExistException,
        "InvalidMinimumHealthyHostValueException": exceptions.InvalidMinimumHealthyHostValueException,
        "ApplicationLimitExceededException": exceptions.ApplicationLimitExceededException,
        "ApplicationNameRequiredException": exceptions.ApplicationNameRequiredException,
        "InvalidEC2TagException": exceptions.InvalidEC2TagException,
        "DeploymentDoesNotExistException": exceptions.DeploymentDoesNotExistException,
        "DeploymentLimitExceededException": exceptions.DeploymentLimitExceededException,
        "InvalidInstanceStatusException": exceptions.InvalidInstanceStatusException,
        "RevisionRequiredException": exceptions.RevisionRequiredException,
        "InvalidBucketNameFilterException": exceptions.InvalidBucketNameFilterException,
        "DeploymentGroupLimitExceededException": exceptions.DeploymentGroupLimitExceededException,
        "DeploymentGroupDoesNotExistException": exceptions.DeploymentGroupDoesNotExistException,
        "DeploymentConfigNameRequiredException": exceptions.DeploymentConfigNameRequiredException,
        "DeploymentAlreadyCompletedException": exceptions.DeploymentAlreadyCompletedException,
        "RevisionDoesNotExistException": exceptions.RevisionDoesNotExistException,
        "DeploymentGroupNameRequiredException": exceptions.DeploymentGroupNameRequiredException,
        "DeploymentIdRequiredException": exceptions.DeploymentIdRequiredException,
        "DeploymentConfigDoesNotExistException": exceptions.DeploymentConfigDoesNotExistException,
        "BucketNameFilterRequiredException": exceptions.BucketNameFilterRequiredException,
        "InvalidTimeRangeException": exceptions.InvalidTimeRangeException,
        "ApplicationDoesNotExistException": exceptions.ApplicationDoesNotExistException,
        "InvalidRevisionException": exceptions.InvalidRevisionException,
        "InvalidSortOrderException": exceptions.InvalidSortOrderException,
        "InvalidOperationException": exceptions.InvalidOperationException,
        "InvalidAutoScalingGroupException": exceptions.InvalidAutoScalingGroupException,
        "InvalidApplicationNameException": exceptions.InvalidApplicationNameException,
        "DescriptionTooLongException": exceptions.DescriptionTooLongException,
        "ApplicationAlreadyExistsException": exceptions.ApplicationAlreadyExistsException,
        "InvalidDeployedStateFilterException": exceptions.InvalidDeployedStateFilterException,
        "DeploymentNotStartedException": exceptions.DeploymentNotStartedException,
        "DeploymentConfigInUseException": exceptions.DeploymentConfigInUseException,
        "InstanceIdRequiredException": exceptions.InstanceIdRequiredException,
        "InvalidKeyPrefixFilterException": exceptions.InvalidKeyPrefixFilterException,
        "InvalidDeploymentStatusException": exceptions.InvalidDeploymentStatusException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(CodeDeployConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def batch_get_applications(self, application_names=None):
        """
        Gets information about one or more applications.

        :type application_names: list
        :param application_names: A list of application names, with multiple
            application names separated by spaces.

        """
        params = {}
        if application_names is not None:
            params['applicationNames'] = application_names
        return self.make_request(action='BatchGetApplications',
                                 body=json.dumps(params))

    def batch_get_deployments(self, deployment_ids=None):
        """
        Gets information about one or more deployments.

        :type deployment_ids: list
        :param deployment_ids: A list of deployment IDs, with multiple
            deployment IDs separated by spaces.

        """
        params = {}
        if deployment_ids is not None:
            params['deploymentIds'] = deployment_ids
        return self.make_request(action='BatchGetDeployments',
                                 body=json.dumps(params))

    def create_application(self, application_name):
        """
        Creates a new application.

        :type application_name: string
        :param application_name: The name of the application. This name must be
            unique within the AWS user account.

        """
        params = {'applicationName': application_name, }
        return self.make_request(action='CreateApplication',
                                 body=json.dumps(params))

    def create_deployment(self, application_name, deployment_group_name=None,
                          revision=None, deployment_config_name=None,
                          description=None,
                          ignore_application_stop_failures=None):
        """
        Deploys an application revision to the specified deployment
        group.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type deployment_group_name: string
        :param deployment_group_name: The deployment group's name.

        :type revision: dict
        :param revision: The type of revision to deploy, along with information
            about the revision's location.

        :type deployment_config_name: string
        :param deployment_config_name: The name of an existing deployment
            configuration within the AWS user account.
        If not specified, the value configured in the deployment group will be
            used as the default. If the deployment group does not have a
            deployment configuration associated with it, then
            CodeDeployDefault.OneAtATime will be used by default.

        :type description: string
        :param description: A comment about the deployment.

        :type ignore_application_stop_failures: boolean
        :param ignore_application_stop_failures: If set to true, then if the
            deployment causes the ApplicationStop deployment lifecycle event to
            fail to a specific instance, the deployment will not be considered
            to have failed to that instance at that point and will continue on
            to the BeforeInstall deployment lifecycle event.
        If set to false or not specified, then if the deployment causes the
            ApplicationStop deployment lifecycle event to fail to a specific
            instance, the deployment will stop to that instance, and the
            deployment to that instance will be considered to have failed.

        """
        params = {'applicationName': application_name, }
        if deployment_group_name is not None:
            params['deploymentGroupName'] = deployment_group_name
        if revision is not None:
            params['revision'] = revision
        if deployment_config_name is not None:
            params['deploymentConfigName'] = deployment_config_name
        if description is not None:
            params['description'] = description
        if ignore_application_stop_failures is not None:
            params['ignoreApplicationStopFailures'] = ignore_application_stop_failures
        return self.make_request(action='CreateDeployment',
                                 body=json.dumps(params))

    def create_deployment_config(self, deployment_config_name,
                                 minimum_healthy_hosts=None):
        """
        Creates a new deployment configuration.

        :type deployment_config_name: string
        :param deployment_config_name: The name of the deployment configuration
            to create.

        :type minimum_healthy_hosts: dict
        :param minimum_healthy_hosts: The minimum number of healthy instances
            that should be available at any time during the deployment. There
            are two parameters expected in the input: type and value.
        The type parameter takes either of the following values:


        + HOST_COUNT: The value parameter represents the minimum number of
              healthy instances, as an absolute value.
        + FLEET_PERCENT: The value parameter represents the minimum number of
              healthy instances, as a percentage of the total number of instances
              in the deployment. If you specify FLEET_PERCENT, then at the start
              of the deployment AWS CodeDeploy converts the percentage to the
              equivalent number of instances and rounds fractional instances up.


        The value parameter takes an integer.

        For example, to set a minimum of 95% healthy instances, specify a type
            of FLEET_PERCENT and a value of 95.

        """
        params = {'deploymentConfigName': deployment_config_name, }
        if minimum_healthy_hosts is not None:
            params['minimumHealthyHosts'] = minimum_healthy_hosts
        return self.make_request(action='CreateDeploymentConfig',
                                 body=json.dumps(params))

    def create_deployment_group(self, application_name,
                                deployment_group_name,
                                deployment_config_name=None,
                                ec_2_tag_filters=None,
                                auto_scaling_groups=None,
                                service_role_arn=None):
        """
        Creates a new deployment group for application revisions to be
        deployed to.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type deployment_group_name: string
        :param deployment_group_name: The name of an existing deployment group
            for the specified application.

        :type deployment_config_name: string
        :param deployment_config_name: If specified, the deployment
            configuration name must be one of the predefined values, or it can
            be a custom deployment configuration:

        + CodeDeployDefault.AllAtOnce deploys an application revision to up to
              all of the Amazon EC2 instances at once. The overall deployment
              succeeds if the application revision deploys to at least one of the
              instances. The overall deployment fails after the application
              revision fails to deploy to all of the instances. For example, for
              9 instances, deploy to up to all 9 instances at once. The overall
              deployment succeeds if any of the 9 instances is successfully
              deployed to, and it fails if all 9 instances fail to be deployed
              to.
        + CodeDeployDefault.HalfAtATime deploys to up to half of the instances
              at a time (with fractions rounded down). The overall deployment
              succeeds if the application revision deploys to at least half of
              the instances (with fractions rounded up); otherwise, the
              deployment fails. For example, for 9 instances, deploy to up to 4
              instances at a time. The overall deployment succeeds if 5 or more
              instances are successfully deployed to; otherwise, the deployment
              fails. Note that the deployment may successfully deploy to some
              instances, even if the overall deployment fails.
        + CodeDeployDefault.OneAtATime deploys the application revision to only
              one of the instances at a time. The overall deployment succeeds if
              the application revision deploys to all of the instances. The
              overall deployment fails after the application revision first fails
              to deploy to any one instance. For example, for 9 instances, deploy
              to one instance at a time. The overall deployment succeeds if all 9
              instances are successfully deployed to, and it fails if any of one
              of the 9 instances fail to be deployed to. Note that the deployment
              may successfully deploy to some instances, even if the overall
              deployment fails. This is the default deployment configuration if a
              configuration isn't specified for either the deployment or the
              deployment group.


        To create a custom deployment configuration, call the create deployment
            configuration operation.

        :type ec_2_tag_filters: list
        :param ec_2_tag_filters: The Amazon EC2 tags to filter on.

        :type auto_scaling_groups: list
        :param auto_scaling_groups: A list of associated Auto Scaling groups.

        :type service_role_arn: string
        :param service_role_arn: A service role ARN that allows AWS CodeDeploy
            to act on the user's behalf when interacting with AWS services.

        """
        params = {
            'applicationName': application_name,
            'deploymentGroupName': deployment_group_name,
        }
        if deployment_config_name is not None:
            params['deploymentConfigName'] = deployment_config_name
        if ec_2_tag_filters is not None:
            params['ec2TagFilters'] = ec_2_tag_filters
        if auto_scaling_groups is not None:
            params['autoScalingGroups'] = auto_scaling_groups
        if service_role_arn is not None:
            params['serviceRoleArn'] = service_role_arn
        return self.make_request(action='CreateDeploymentGroup',
                                 body=json.dumps(params))

    def delete_application(self, application_name):
        """
        Deletes an application.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        """
        params = {'applicationName': application_name, }
        return self.make_request(action='DeleteApplication',
                                 body=json.dumps(params))

    def delete_deployment_config(self, deployment_config_name):
        """
        Deletes a deployment configuration.

        A deployment configuration cannot be deleted if it is
        currently in use. Also, predefined configurations cannot be
        deleted.

        :type deployment_config_name: string
        :param deployment_config_name: The name of an existing deployment
            configuration within the AWS user account.

        """
        params = {'deploymentConfigName': deployment_config_name, }
        return self.make_request(action='DeleteDeploymentConfig',
                                 body=json.dumps(params))

    def delete_deployment_group(self, application_name,
                                deployment_group_name):
        """
        Deletes a deployment group.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type deployment_group_name: string
        :param deployment_group_name: The name of an existing deployment group
            for the specified application.

        """
        params = {
            'applicationName': application_name,
            'deploymentGroupName': deployment_group_name,
        }
        return self.make_request(action='DeleteDeploymentGroup',
                                 body=json.dumps(params))

    def get_application(self, application_name):
        """
        Gets information about an application.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        """
        params = {'applicationName': application_name, }
        return self.make_request(action='GetApplication',
                                 body=json.dumps(params))

    def get_application_revision(self, application_name, revision):
        """
        Gets information about an application revision.

        :type application_name: string
        :param application_name: The name of the application that corresponds
            to the revision.

        :type revision: dict
        :param revision: Information about the application revision to get,
            including the revision's type and its location.

        """
        params = {
            'applicationName': application_name,
            'revision': revision,
        }
        return self.make_request(action='GetApplicationRevision',
                                 body=json.dumps(params))

    def get_deployment(self, deployment_id):
        """
        Gets information about a deployment.

        :type deployment_id: string
        :param deployment_id: An existing deployment ID within the AWS user
            account.

        """
        params = {'deploymentId': deployment_id, }
        return self.make_request(action='GetDeployment',
                                 body=json.dumps(params))

    def get_deployment_config(self, deployment_config_name):
        """
        Gets information about a deployment configuration.

        :type deployment_config_name: string
        :param deployment_config_name: The name of an existing deployment
            configuration within the AWS user account.

        """
        params = {'deploymentConfigName': deployment_config_name, }
        return self.make_request(action='GetDeploymentConfig',
                                 body=json.dumps(params))

    def get_deployment_group(self, application_name, deployment_group_name):
        """
        Gets information about a deployment group.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type deployment_group_name: string
        :param deployment_group_name: The name of an existing deployment group
            for the specified application.

        """
        params = {
            'applicationName': application_name,
            'deploymentGroupName': deployment_group_name,
        }
        return self.make_request(action='GetDeploymentGroup',
                                 body=json.dumps(params))

    def get_deployment_instance(self, deployment_id, instance_id):
        """
        Gets information about an Amazon EC2 instance as part of a
        deployment.

        :type deployment_id: string
        :param deployment_id: The unique ID of a deployment.

        :type instance_id: string
        :param instance_id: The unique ID of an Amazon EC2 instance in the
            deployment's deployment group.

        """
        params = {
            'deploymentId': deployment_id,
            'instanceId': instance_id,
        }
        return self.make_request(action='GetDeploymentInstance',
                                 body=json.dumps(params))

    def list_application_revisions(self, application_name, sort_by=None,
                                   sort_order=None, s_3_bucket=None,
                                   s_3_key_prefix=None, deployed=None,
                                   next_token=None):
        """
        Lists information about revisions for an application.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type sort_by: string
        :param sort_by: The column name to sort the list results by:

        + registerTime: Sort the list results by when the revisions were
              registered with AWS CodeDeploy.
        + firstUsedTime: Sort the list results by when the revisions were first
              used by in a deployment.
        + lastUsedTime: Sort the list results by when the revisions were last
              used in a deployment.


        If not specified or set to null, the results will be returned in an
            arbitrary order.

        :type sort_order: string
        :param sort_order: The order to sort the list results by:

        + ascending: Sort the list results in ascending order.
        + descending: Sort the list results in descending order.


        If not specified, the results will be sorted in ascending order.

        If set to null, the results will be sorted in an arbitrary order.

        :type s_3_bucket: string
        :param s_3_bucket: A specific Amazon S3 bucket name to limit the search
            for revisions.
        If set to null, then all of the user's buckets will be searched.

        :type s_3_key_prefix: string
        :param s_3_key_prefix: A specific key prefix for the set of Amazon S3
            objects to limit the search for revisions.

        :type deployed: string
        :param deployed:
        Whether to list revisions based on whether the revision is the target
            revision of an deployment group:


        + include: List revisions that are target revisions of a deployment
              group.
        + exclude: Do not list revisions that are target revisions of a
              deployment group.
        + ignore: List all revisions, regardless of whether they are target
              revisions of a deployment group.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list application revisions call, which can be used to return the
            next set of applications in the list.

        """
        params = {'applicationName': application_name, }
        if sort_by is not None:
            params['sortBy'] = sort_by
        if sort_order is not None:
            params['sortOrder'] = sort_order
        if s_3_bucket is not None:
            params['s3Bucket'] = s_3_bucket
        if s_3_key_prefix is not None:
            params['s3KeyPrefix'] = s_3_key_prefix
        if deployed is not None:
            params['deployed'] = deployed
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='ListApplicationRevisions',
                                 body=json.dumps(params))

    def list_applications(self, next_token=None):
        """
        Lists the applications registered within the AWS user account.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list applications call, which can be used to return the next set of
            applications in the list.

        """
        params = {}
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='ListApplications',
                                 body=json.dumps(params))

    def list_deployment_configs(self, next_token=None):
        """
        Lists the deployment configurations within the AWS user
        account.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list deployment configurations call, which can be used to return
            the next set of deployment configurations in the list.

        """
        params = {}
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='ListDeploymentConfigs',
                                 body=json.dumps(params))

    def list_deployment_groups(self, application_name, next_token=None):
        """
        Lists the deployment groups for an application registered
        within the AWS user account.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list deployment groups call, which can be used to return the next
            set of deployment groups in the list.

        """
        params = {'applicationName': application_name, }
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='ListDeploymentGroups',
                                 body=json.dumps(params))

    def list_deployment_instances(self, deployment_id, next_token=None,
                                  instance_status_filter=None):
        """
        Lists the Amazon EC2 instances for a deployment within the AWS
        user account.

        :type deployment_id: string
        :param deployment_id: The unique ID of a deployment.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list deployment instances call, which can be used to return the
            next set of deployment instances in the list.

        :type instance_status_filter: list
        :param instance_status_filter:
        A subset of instances to list, by status:


        + Pending: Include in the resulting list those instances with pending
              deployments.
        + InProgress: Include in the resulting list those instances with in-
              progress deployments.
        + Succeeded: Include in the resulting list those instances with
              succeeded deployments.
        + Failed: Include in the resulting list those instances with failed
              deployments.
        + Skipped: Include in the resulting list those instances with skipped
              deployments.
        + Unknown: Include in the resulting list those instances with
              deployments in an unknown state.

        """
        params = {'deploymentId': deployment_id, }
        if next_token is not None:
            params['nextToken'] = next_token
        if instance_status_filter is not None:
            params['instanceStatusFilter'] = instance_status_filter
        return self.make_request(action='ListDeploymentInstances',
                                 body=json.dumps(params))

    def list_deployments(self, application_name=None,
                         deployment_group_name=None,
                         include_only_statuses=None, create_time_range=None,
                         next_token=None):
        """
        Lists the deployments under a deployment group for an
        application registered within the AWS user account.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type deployment_group_name: string
        :param deployment_group_name: The name of an existing deployment group
            for the specified application.

        :type include_only_statuses: list
        :param include_only_statuses: A subset of deployments to list, by
            status:

        + Created: Include in the resulting list created deployments.
        + Queued: Include in the resulting list queued deployments.
        + In Progress: Include in the resulting list in-progress deployments.
        + Succeeded: Include in the resulting list succeeded deployments.
        + Failed: Include in the resulting list failed deployments.
        + Aborted: Include in the resulting list aborted deployments.

        :type create_time_range: dict
        :param create_time_range: A deployment creation start- and end-time
            range for returning a subset of the list of deployments.

        :type next_token: string
        :param next_token: An identifier that was returned from the previous
            list deployments call, which can be used to return the next set of
            deployments in the list.

        """
        params = {}
        if application_name is not None:
            params['applicationName'] = application_name
        if deployment_group_name is not None:
            params['deploymentGroupName'] = deployment_group_name
        if include_only_statuses is not None:
            params['includeOnlyStatuses'] = include_only_statuses
        if create_time_range is not None:
            params['createTimeRange'] = create_time_range
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='ListDeployments',
                                 body=json.dumps(params))

    def register_application_revision(self, application_name, revision,
                                      description=None):
        """
        Registers with AWS CodeDeploy a revision for the specified
        application.

        :type application_name: string
        :param application_name: The name of an existing AWS CodeDeploy
            application within the AWS user account.

        :type description: string
        :param description: A comment about the revision.

        :type revision: dict
        :param revision: Information about the application revision to
            register, including the revision's type and its location.

        """
        params = {
            'applicationName': application_name,
            'revision': revision,
        }
        if description is not None:
            params['description'] = description
        return self.make_request(action='RegisterApplicationRevision',
                                 body=json.dumps(params))

    def stop_deployment(self, deployment_id):
        """
        Attempts to stop an ongoing deployment.

        :type deployment_id: string
        :param deployment_id: The unique ID of a deployment.

        """
        params = {'deploymentId': deployment_id, }
        return self.make_request(action='StopDeployment',
                                 body=json.dumps(params))

    def update_application(self, application_name=None,
                           new_application_name=None):
        """
        Changes an existing application's name.

        :type application_name: string
        :param application_name: The current name of the application that you
            want to change.

        :type new_application_name: string
        :param new_application_name: The new name that you want to change the
            application to.

        """
        params = {}
        if application_name is not None:
            params['applicationName'] = application_name
        if new_application_name is not None:
            params['newApplicationName'] = new_application_name
        return self.make_request(action='UpdateApplication',
                                 body=json.dumps(params))

    def update_deployment_group(self, application_name,
                                current_deployment_group_name,
                                new_deployment_group_name=None,
                                deployment_config_name=None,
                                ec_2_tag_filters=None,
                                auto_scaling_groups=None,
                                service_role_arn=None):
        """
        Changes information about an existing deployment group.

        :type application_name: string
        :param application_name: The application name corresponding to the
            deployment group to update.

        :type current_deployment_group_name: string
        :param current_deployment_group_name: The current name of the existing
            deployment group.

        :type new_deployment_group_name: string
        :param new_deployment_group_name: The new name of the deployment group,
            if you want to change it.

        :type deployment_config_name: string
        :param deployment_config_name: The replacement deployment configuration
            name to use, if you want to change it.

        :type ec_2_tag_filters: list
        :param ec_2_tag_filters: The replacement set of Amazon EC2 tags to
            filter on, if you want to change them.

        :type auto_scaling_groups: list
        :param auto_scaling_groups: The replacement list of Auto Scaling groups
            to be included in the deployment group, if you want to change them.

        :type service_role_arn: string
        :param service_role_arn: A replacement service role's ARN, if you want
            to change it.

        """
        params = {
            'applicationName': application_name,
            'currentDeploymentGroupName': current_deployment_group_name,
        }
        if new_deployment_group_name is not None:
            params['newDeploymentGroupName'] = new_deployment_group_name
        if deployment_config_name is not None:
            params['deploymentConfigName'] = deployment_config_name
        if ec_2_tag_filters is not None:
            params['ec2TagFilters'] = ec_2_tag_filters
        if auto_scaling_groups is not None:
            params['autoScalingGroups'] = auto_scaling_groups
        if service_role_arn is not None:
            params['serviceRoleArn'] = service_role_arn
        return self.make_request(action='UpdateDeploymentGroup',
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

