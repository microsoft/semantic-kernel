# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
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

import boto
import boto.jsonresponse
from boto.compat import json
from boto.regioninfo import RegionInfo
from boto.connection import AWSQueryConnection


class Layer1(AWSQueryConnection):

    APIVersion = '2010-12-01'
    DefaultRegionName = 'us-east-1'
    DefaultRegionEndpoint = 'elasticbeanstalk.us-east-1.amazonaws.com'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 api_version=None, security_token=None, profile_name=None):
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region
        super(Layer1, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    security_token, profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def _encode_bool(self, v):
        v = bool(v)
        return {True: "true", False: "false"}[v]

    def _get_response(self, action, params, path='/', verb='GET'):
        params['ContentType'] = 'JSON'
        response = self.make_request(action, params, path, verb)
        body = response.read().decode('utf-8')
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            raise self.ResponseError(response.status, response.reason, body)

    def check_dns_availability(self, cname_prefix):
        """Checks if the specified CNAME is available.

        :type cname_prefix: string
        :param cname_prefix: The prefix used when this CNAME is
            reserved.
        """
        params = {'CNAMEPrefix': cname_prefix}
        return self._get_response('CheckDNSAvailability', params)

    def create_application(self, application_name, description=None):
        """
        Creates an application that has one configuration template
        named default and no application versions.

        :type application_name: string
        :param application_name: The name of the application.
            Constraint: This name must be unique within your account. If the
            specified name already exists, the action returns an
            InvalidParameterValue error.

        :type description: string
        :param description: Describes the application.

        :raises: TooManyApplicationsException
        """
        params = {'ApplicationName': application_name}
        if description:
            params['Description'] = description
        return self._get_response('CreateApplication', params)

    def create_application_version(self, application_name, version_label,
                                   description=None, s3_bucket=None,
                                   s3_key=None, auto_create_application=None):
        """Creates an application version for the specified application.

        :type application_name: string
        :param application_name: The name of the application. If no
            application is found with this name, and AutoCreateApplication is
            false, returns an InvalidParameterValue error.

        :type version_label: string
        :param version_label: A label identifying this version. Constraint:
            Must be unique per application. If an application version already
            exists with this label for the specified application, AWS Elastic
            Beanstalk returns an InvalidParameterValue error.

        :type description: string
        :param description: Describes this version.

        :type s3_bucket: string
        :param s3_bucket: The Amazon S3 bucket where the data is located.

        :type s3_key: string
        :param s3_key: The Amazon S3 key where the data is located.  Both
            s3_bucket and s3_key must be specified in order to use a specific
            source bundle.  If both of these values are not specified the
            sample application will be used.

        :type auto_create_application: boolean
        :param auto_create_application: Determines how the system behaves if
            the specified application for this version does not already exist:
            true: Automatically creates the specified application for this
            version if it does not already exist.  false: Returns an
            InvalidParameterValue if the specified application for this version
            does not already exist.  Default: false  Valid Values: true | false

        :raises: TooManyApplicationsException,
                 TooManyApplicationVersionsException,
                 InsufficientPrivilegesException,
                 S3LocationNotInServiceRegionException

        """
        params = {'ApplicationName': application_name,
                  'VersionLabel': version_label}
        if description:
            params['Description'] = description
        if s3_bucket and s3_key:
            params['SourceBundle.S3Bucket'] = s3_bucket
            params['SourceBundle.S3Key'] = s3_key
        if auto_create_application:
            params['AutoCreateApplication'] = self._encode_bool(
                auto_create_application)
        return self._get_response('CreateApplicationVersion', params)

    def create_configuration_template(self, application_name, template_name,
                                      solution_stack_name=None,
                                      source_configuration_application_name=None,
                                      source_configuration_template_name=None,
                                      environment_id=None, description=None,
                                      option_settings=None):
        """Creates a configuration template.

        Templates are associated with a specific application and are used to
        deploy different versions of the application with the same
        configuration settings.

        :type application_name: string
        :param application_name: The name of the application to associate with
            this configuration template. If no application is found with this
            name, AWS Elastic Beanstalk returns an InvalidParameterValue error.

        :type template_name: string
        :param template_name: The name of the configuration template.
            Constraint: This name must be unique per application.  Default: If
            a configuration template already exists with this name, AWS Elastic
            Beanstalk returns an InvalidParameterValue error.

        :type solution_stack_name: string
        :param solution_stack_name: The name of the solution stack used by this
            configuration. The solution stack specifies the operating system,
            architecture, and application server for a configuration template.
            It determines the set of configuration options as well as the
            possible and default values.  Use ListAvailableSolutionStacks to
            obtain a list of available solution stacks.  Default: If the
            SolutionStackName is not specified and the source configuration
            parameter is blank, AWS Elastic Beanstalk uses the default solution
            stack. If not specified and the source configuration parameter is
            specified, AWS Elastic Beanstalk uses the same solution stack as
            the source configuration template.

        :type source_configuration_application_name: string
        :param source_configuration_application_name: The name of the
            application associated with the configuration.

        :type source_configuration_template_name: string
        :param source_configuration_template_name: The name of the
            configuration template.

        :type environment_id: string
        :param environment_id: The ID of the environment used with this
            configuration template.

        :type description: string
        :param description: Describes this configuration.

        :type option_settings: list
        :param option_settings: If specified, AWS Elastic Beanstalk sets the
            specified configuration option to the requested value. The new
            value overrides the value obtained from the solution stack or the
            source configuration template.

        :raises: InsufficientPrivilegesException,
                 TooManyConfigurationTemplatesException
        """
        params = {'ApplicationName': application_name,
                  'TemplateName': template_name}
        if solution_stack_name:
            params['SolutionStackName'] = solution_stack_name
        if source_configuration_application_name:
            params['SourceConfiguration.ApplicationName'] = source_configuration_application_name
        if source_configuration_template_name:
            params['SourceConfiguration.TemplateName'] = source_configuration_template_name
        if environment_id:
            params['EnvironmentId'] = environment_id
        if description:
            params['Description'] = description
        if option_settings:
            self._build_list_params(params, option_settings,
                                   'OptionSettings.member',
                                   ('Namespace', 'OptionName', 'Value'))
        return self._get_response('CreateConfigurationTemplate', params)

    def create_environment(self, application_name, environment_name,
                           version_label=None, template_name=None,
                           solution_stack_name=None, cname_prefix=None,
                           description=None, option_settings=None,
                           options_to_remove=None, tier_name=None,
                           tier_type=None, tier_version='1.0'):
        """Launches an environment for the application using a configuration.

        :type application_name: string
        :param application_name: The name of the application that contains the
            version to be deployed.  If no application is found with this name,
            CreateEnvironment returns an InvalidParameterValue error.

        :type environment_name: string
        :param environment_name: A unique name for the deployment environment.
            Used in the application URL. Constraint: Must be from 4 to 23
            characters in length. The name can contain only letters, numbers,
            and hyphens. It cannot start or end with a hyphen. This name must
            be unique in your account. If the specified name already exists,
            AWS Elastic Beanstalk returns an InvalidParameterValue error.
            Default: If the CNAME parameter is not specified, the environment
            name becomes part of the CNAME, and therefore part of the visible
            URL for your application.

        :type version_label: string
        :param version_label: The name of the application version to deploy. If
            the specified application has no associated application versions,
            AWS Elastic Beanstalk UpdateEnvironment returns an
            InvalidParameterValue error.  Default: If not specified, AWS
            Elastic Beanstalk attempts to launch the most recently created
            application version.

        :type template_name: string
        :param template_name: The name of the configuration template to
            use in deployment. If no configuration template is found with this
            name, AWS Elastic Beanstalk returns an InvalidParameterValue error.
            Condition: You must specify either this parameter or a
            SolutionStackName, but not both. If you specify both, AWS Elastic
            Beanstalk returns an InvalidParameterCombination error. If you do
            not specify either, AWS Elastic Beanstalk returns a
            MissingRequiredParameter error.

        :type solution_stack_name: string
        :param solution_stack_name: This is an alternative to specifying a
            configuration name. If specified, AWS Elastic Beanstalk sets the
            configuration values to the default values associated with the
            specified solution stack.  Condition: You must specify either this
            or a TemplateName, but not both. If you specify both, AWS Elastic
            Beanstalk returns an InvalidParameterCombination error. If you do
            not specify either, AWS Elastic Beanstalk returns a
            MissingRequiredParameter error.

        :type cname_prefix: string
        :param cname_prefix: If specified, the environment attempts to use this
            value as the prefix for the CNAME. If not specified, the
            environment uses the environment name.

        :type description: string
        :param description: Describes this environment.

        :type option_settings: list
        :param option_settings: If specified, AWS Elastic Beanstalk sets the
            specified configuration options to the requested value in the
            configuration set for the new environment. These override the
            values obtained from the solution stack or the configuration
            template.  Each element in the list is a tuple of (Namespace,
            OptionName, Value), for example::

                [('aws:autoscaling:launchconfiguration',
                    'Ec2KeyName', 'mykeypair')]

        :type options_to_remove: list
        :param options_to_remove: A list of custom user-defined configuration
            options to remove from the configuration set for this new
            environment.

        :type tier_name: string
        :param tier_name: The name of the tier.  Valid values are
            "WebServer" and "Worker". Defaults to "WebServer".
            The ``tier_name`` and a ``tier_type`` parameters are
            related and the values provided must be valid.
            The possible combinations are:

              * "WebServer" and "Standard" (the default)
              * "Worker" and "SQS/HTTP"

        :type tier_type: string
        :param tier_type: The type of the tier.  Valid values are
            "Standard" if ``tier_name`` is "WebServer" and "SQS/HTTP"
            if ``tier_name`` is "Worker". Defaults to "Standard".

        :type tier_version: string
        :type tier_version: The version of the tier.  Valid values
            currently are "1.0". Defaults to "1.0".

        :raises: TooManyEnvironmentsException, InsufficientPrivilegesException

        """
        params = {'ApplicationName': application_name,
                  'EnvironmentName': environment_name}
        if version_label:
            params['VersionLabel'] = version_label
        if template_name:
            params['TemplateName'] = template_name
        if solution_stack_name:
            params['SolutionStackName'] = solution_stack_name
        if cname_prefix:
            params['CNAMEPrefix'] = cname_prefix
        if description:
            params['Description'] = description
        if option_settings:
            self._build_list_params(params, option_settings,
                                   'OptionSettings.member',
                                   ('Namespace', 'OptionName', 'Value'))
        if options_to_remove:
            self.build_list_params(params, options_to_remove,
                                   'OptionsToRemove.member')
        if tier_name and tier_type and tier_version:
            params['Tier.Name'] = tier_name
            params['Tier.Type'] = tier_type
            params['Tier.Version'] = tier_version
        return self._get_response('CreateEnvironment', params)

    def create_storage_location(self):
        """
        Creates the Amazon S3 storage location for the account.  This
        location is used to store user log files.

        :raises: TooManyBucketsException,
                 S3SubscriptionRequiredException,
                 InsufficientPrivilegesException

        """
        return self._get_response('CreateStorageLocation', params={})

    def delete_application(self, application_name,
                           terminate_env_by_force=None):
        """
        Deletes the specified application along with all associated
        versions and configurations. The application versions will not
        be deleted from your Amazon S3 bucket.

        :type application_name: string
        :param application_name: The name of the application to delete.

        :type terminate_env_by_force: boolean
        :param terminate_env_by_force: When set to true, running
            environments will be terminated before deleting the application.

        :raises: OperationInProgressException

        """
        params = {'ApplicationName': application_name}
        if terminate_env_by_force:
            params['TerminateEnvByForce'] = self._encode_bool(
                terminate_env_by_force)
        return self._get_response('DeleteApplication', params)

    def delete_application_version(self, application_name, version_label,
                                   delete_source_bundle=None):
        """Deletes the specified version from the specified application.

        :type application_name: string
        :param application_name: The name of the application to delete
            releases from.

        :type version_label: string
        :param version_label: The label of the version to delete.

        :type delete_source_bundle: boolean
        :param delete_source_bundle: Indicates whether to delete the
            associated source bundle from Amazon S3.  Valid Values: true |
            false

        :raises: SourceBundleDeletionException,
                 InsufficientPrivilegesException,
                 OperationInProgressException,
                 S3LocationNotInServiceRegionException
        """
        params = {'ApplicationName': application_name,
                  'VersionLabel': version_label}
        if delete_source_bundle:
            params['DeleteSourceBundle'] = self._encode_bool(
                delete_source_bundle)
        return self._get_response('DeleteApplicationVersion', params)

    def delete_configuration_template(self, application_name, template_name):
        """Deletes the specified configuration template.

        :type application_name: string
        :param application_name: The name of the application to delete
            the configuration template from.

        :type template_name: string
        :param template_name: The name of the configuration template to
            delete.

        :raises: OperationInProgressException

        """
        params = {'ApplicationName': application_name,
                  'TemplateName': template_name}
        return self._get_response('DeleteConfigurationTemplate', params)

    def delete_environment_configuration(self, application_name,
                                         environment_name):
        """
        Deletes the draft configuration associated with the running
        environment.  Updating a running environment with any
        configuration changes creates a draft configuration set. You can
        get the draft configuration using DescribeConfigurationSettings
        while the update is in progress or if the update fails. The
        DeploymentStatus for the draft configuration indicates whether
        the deployment is in process or has failed. The draft
        configuration remains in existence until it is deleted with this
        action.

        :type application_name: string
        :param application_name: The name of the application the
            environment is associated with.

        :type environment_name: string
        :param environment_name: The name of the environment to delete
            the draft configuration from.

        """
        params = {'ApplicationName': application_name,
                  'EnvironmentName': environment_name}
        return self._get_response('DeleteEnvironmentConfiguration', params)

    def describe_application_versions(self, application_name=None,
                                      version_labels=None):
        """Returns descriptions for existing application versions.

        :type application_name: string
        :param application_name: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to only include ones that are associated
            with the specified application.

        :type version_labels: list
        :param version_labels: If specified, restricts the returned
            descriptions to only include ones that have the specified version
            labels.

        """
        params = {}
        if application_name:
            params['ApplicationName'] = application_name
        if version_labels:
            self.build_list_params(params, version_labels,
                                   'VersionLabels.member')
        return self._get_response('DescribeApplicationVersions', params)

    def describe_applications(self, application_names=None):
        """Returns the descriptions of existing applications.

        :type application_names: list
        :param application_names: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to only include those with the specified
            names.

        """
        params = {}
        if application_names:
            self.build_list_params(params, application_names,
                                   'ApplicationNames.member')
        return self._get_response('DescribeApplications', params)

    def describe_configuration_options(self, application_name=None,
                                       template_name=None,
                                       environment_name=None,
                                       solution_stack_name=None, options=None):
        """Describes configuration options used in a template or environment.

        Describes the configuration options that are used in a
        particular configuration template or environment, or that a
        specified solution stack defines. The description includes the
        values the options, their default values, and an indication of
        the required action on a running environment if an option value
        is changed.

        :type application_name: string
        :param application_name: The name of the application associated with
            the configuration template or environment. Only needed if you want
            to describe the configuration options associated with either the
            configuration template or environment.

        :type template_name: string
        :param template_name: The name of the configuration template whose
            configuration options you want to describe.

        :type environment_name: string
        :param environment_name: The name of the environment whose
            configuration options you want to describe.

        :type solution_stack_name: string
        :param solution_stack_name: The name of the solution stack whose
            configuration options you want to describe.

        :type options: list
        :param options: If specified, restricts the descriptions to only
            the specified options.
        """
        params = {}
        if application_name:
            params['ApplicationName'] = application_name
        if template_name:
            params['TemplateName'] = template_name
        if environment_name:
            params['EnvironmentName'] = environment_name
        if solution_stack_name:
            params['SolutionStackName'] = solution_stack_name
        if options:
            self.build_list_params(params, options, 'Options.member')
        return self._get_response('DescribeConfigurationOptions', params)

    def describe_configuration_settings(self, application_name,
                                        template_name=None,
                                        environment_name=None):
        """
        Returns a description of the settings for the specified
        configuration set, that is, either a configuration template or
        the configuration set associated with a running environment.
        When describing the settings for the configuration set
        associated with a running environment, it is possible to receive
        two sets of setting descriptions. One is the deployed
        configuration set, and the other is a draft configuration of an
        environment that is either in the process of deployment or that
        failed to deploy.

        :type application_name: string
        :param application_name: The application for the environment or
            configuration template.

        :type template_name: string
        :param template_name: The name of the configuration template to
            describe.  Conditional: You must specify either this parameter or
            an EnvironmentName, but not both. If you specify both, AWS Elastic
            Beanstalk returns an InvalidParameterCombination error.  If you do
            not specify either, AWS Elastic Beanstalk returns a
            MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to describe.
            Condition: You must specify either this or a TemplateName, but not
            both. If you specify both, AWS Elastic Beanstalk returns an
            InvalidParameterCombination error. If you do not specify either,
            AWS Elastic Beanstalk returns MissingRequiredParameter error.
        """
        params = {'ApplicationName': application_name}
        if template_name:
            params['TemplateName'] = template_name
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('DescribeConfigurationSettings', params)

    def describe_environment_resources(self, environment_id=None,
                                       environment_name=None):
        """Returns AWS resources for this environment.

        :type environment_id: string
        :param environment_id: The ID of the environment to retrieve AWS
            resource usage data.  Condition: You must specify either this or an
            EnvironmentName, or both. If you do not specify either, AWS Elastic
            Beanstalk returns MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to retrieve
            AWS resource usage data.  Condition: You must specify either this
            or an EnvironmentId, or both. If you do not specify either, AWS
            Elastic Beanstalk returns MissingRequiredParameter error.

        :raises: InsufficientPrivilegesException
        """
        params = {}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('DescribeEnvironmentResources', params)

    def describe_environments(self, application_name=None, version_label=None,
                              environment_ids=None, environment_names=None,
                              include_deleted=None,
                              included_deleted_back_to=None):
        """Returns descriptions for existing environments.

        :type application_name: string
        :param application_name: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to include only those that are associated
            with this application.

        :type version_label: string
        :param version_label: If specified, AWS Elastic Beanstalk restricts the
            returned descriptions to include only those that are associated
            with this application version.

        :type environment_ids: list
        :param environment_ids: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to include only those that have the
            specified IDs.

        :type environment_names: list
        :param environment_names: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to include only those that have the
            specified names.

        :type include_deleted: boolean
        :param include_deleted: Indicates whether to include deleted
            environments:  true: Environments that have been deleted after
            IncludedDeletedBackTo are displayed.  false: Do not include deleted
            environments.

        :type included_deleted_back_to: timestamp
        :param included_deleted_back_to: If specified when IncludeDeleted is
            set to true, then environments deleted after this date are
            displayed.
        """
        params = {}
        if application_name:
            params['ApplicationName'] = application_name
        if version_label:
            params['VersionLabel'] = version_label
        if environment_ids:
            self.build_list_params(params, environment_ids,
                                   'EnvironmentIds.member')
        if environment_names:
            self.build_list_params(params, environment_names,
                                   'EnvironmentNames.member')
        if include_deleted:
            params['IncludeDeleted'] = self._encode_bool(include_deleted)
        if included_deleted_back_to:
            params['IncludedDeletedBackTo'] = included_deleted_back_to
        return self._get_response('DescribeEnvironments', params)

    def describe_events(self, application_name=None, version_label=None,
                        template_name=None, environment_id=None,
                        environment_name=None, request_id=None, severity=None,
                        start_time=None, end_time=None, max_records=None,
                        next_token=None):
        """Returns event descriptions matching criteria up to the last 6 weeks.

        :type application_name: string
        :param application_name: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to include only those associated with
            this application.

        :type version_label: string
        :param version_label: If specified, AWS Elastic Beanstalk restricts the
            returned descriptions to those associated with this application
            version.

        :type template_name: string
        :param template_name: If specified, AWS Elastic Beanstalk restricts the
            returned descriptions to those that are associated with this
            environment configuration.

        :type environment_id: string
        :param environment_id: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to those associated with this
            environment.

        :type environment_name: string
        :param environment_name: If specified, AWS Elastic Beanstalk restricts
            the returned descriptions to those associated with this
            environment.

        :type request_id: string
        :param request_id: If specified, AWS Elastic Beanstalk restricts the
            described events to include only those associated with this request
            ID.

        :type severity: string
        :param severity: If specified, limits the events returned from this
            call to include only those with the specified severity or higher.

        :type start_time: timestamp
        :param start_time: If specified, AWS Elastic Beanstalk restricts the
            returned descriptions to those that occur on or after this time.

        :type end_time: timestamp
        :param end_time: If specified, AWS Elastic Beanstalk restricts the
            returned descriptions to those that occur up to, but not including,
            the EndTime.

        :type max_records: integer
        :param max_records: Specifies the maximum number of events that can be
            returned, beginning with the most recent event.

        :type next_token: string
        :param next_token: Pagination token. If specified, the events return
            the next batch of results.
        """
        params = {}
        if application_name:
            params['ApplicationName'] = application_name
        if version_label:
            params['VersionLabel'] = version_label
        if template_name:
            params['TemplateName'] = template_name
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        if request_id:
            params['RequestId'] = request_id
        if severity:
            params['Severity'] = severity
        if start_time:
            params['StartTime'] = start_time
        if end_time:
            params['EndTime'] = end_time
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self._get_response('DescribeEvents', params)

    def list_available_solution_stacks(self):
        """Returns a list of the available solution stack names."""
        return self._get_response('ListAvailableSolutionStacks', params={})

    def rebuild_environment(self, environment_id=None, environment_name=None):
        """
        Deletes and recreates all of the AWS resources (for example:
        the Auto Scaling group, load balancer, etc.) for a specified
        environment and forces a restart.

        :type environment_id: string
        :param environment_id: The ID of the environment to rebuild.
            Condition: You must specify either this or an EnvironmentName, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to rebuild.
            Condition: You must specify either this or an EnvironmentId, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :raises InvalidParameterValue: If environment_name doesn't refer to a currently active environment
        :raises: InsufficientPrivilegesException
        """
        params = {}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('RebuildEnvironment', params)

    def request_environment_info(self, info_type='tail', environment_id=None,
                                 environment_name=None):
        """
        Initiates a request to compile the specified type of
        information of the deployed environment.  Setting the InfoType
        to tail compiles the last lines from the application server log
        files of every Amazon EC2 instance in your environment. Use
        RetrieveEnvironmentInfo to access the compiled information.

        :type info_type: string
        :param info_type: The type of information to request.

        :type environment_id: string
        :param environment_id: The ID of the environment of the
            requested data. If no such environment is found,
            RequestEnvironmentInfo returns an InvalidParameterValue error.
            Condition: You must specify either this or an EnvironmentName, or
            both. If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment of the
            requested data. If no such environment is found,
            RequestEnvironmentInfo returns an InvalidParameterValue error.
            Condition: You must specify either this or an EnvironmentId, or
            both. If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.
        """
        params = {'InfoType': info_type}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('RequestEnvironmentInfo', params)

    def restart_app_server(self, environment_id=None, environment_name=None):
        """
        Causes the environment to restart the application container
        server running on each Amazon EC2 instance.

        :type environment_id: string
        :param environment_id: The ID of the environment to restart the server
            for.  Condition: You must specify either this or an
            EnvironmentName, or both. If you do not specify either, AWS Elastic
            Beanstalk returns MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to restart the
            server for.  Condition: You must specify either this or an
            EnvironmentId, or both. If you do not specify either, AWS Elastic
            Beanstalk returns MissingRequiredParameter error.
        """
        params = {}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('RestartAppServer', params)

    def retrieve_environment_info(self, info_type='tail', environment_id=None,
                                  environment_name=None):
        """
        Retrieves the compiled information from a RequestEnvironmentInfo
        request.

        :type info_type: string
        :param info_type: The type of information to retrieve.

        :type environment_id: string
        :param environment_id: The ID of the data's environment. If no such
            environment is found, returns an InvalidParameterValue error.
            Condition: You must specify either this or an EnvironmentName, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the data's environment. If no such
            environment is found, returns an InvalidParameterValue error.
            Condition: You must specify either this or an EnvironmentId, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.
        """
        params = {'InfoType': info_type}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('RetrieveEnvironmentInfo', params)

    def swap_environment_cnames(self, source_environment_id=None,
                                source_environment_name=None,
                                destination_environment_id=None,
                                destination_environment_name=None):
        """Swaps the CNAMEs of two environments.

        :type source_environment_id: string
        :param source_environment_id: The ID of the source environment.
            Condition: You must specify at least the SourceEnvironmentID or the
            SourceEnvironmentName. You may also specify both. If you specify
            the SourceEnvironmentId, you must specify the
            DestinationEnvironmentId.

        :type source_environment_name: string
        :param source_environment_name: The name of the source environment.
            Condition: You must specify at least the SourceEnvironmentID or the
            SourceEnvironmentName. You may also specify both. If you specify
            the SourceEnvironmentName, you must specify the
            DestinationEnvironmentName.

        :type destination_environment_id: string
        :param destination_environment_id: The ID of the destination
            environment.  Condition: You must specify at least the
            DestinationEnvironmentID or the DestinationEnvironmentName. You may
            also specify both. You must specify the SourceEnvironmentId with
            the DestinationEnvironmentId.

        :type destination_environment_name: string
        :param destination_environment_name: The name of the destination
            environment.  Condition: You must specify at least the
            DestinationEnvironmentID or the DestinationEnvironmentName. You may
            also specify both. You must specify the SourceEnvironmentName with
            the DestinationEnvironmentName.
        """
        params = {}
        if source_environment_id:
            params['SourceEnvironmentId'] = source_environment_id
        if source_environment_name:
            params['SourceEnvironmentName'] = source_environment_name
        if destination_environment_id:
            params['DestinationEnvironmentId'] = destination_environment_id
        if destination_environment_name:
            params['DestinationEnvironmentName'] = destination_environment_name
        return self._get_response('SwapEnvironmentCNAMEs', params)

    def terminate_environment(self, environment_id=None, environment_name=None,
                              terminate_resources=None):
        """Terminates the specified environment.

        :type environment_id: string
        :param environment_id: The ID of the environment to terminate.
            Condition: You must specify either this or an EnvironmentName, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to terminate.
            Condition: You must specify either this or an EnvironmentId, or
            both.  If you do not specify either, AWS Elastic Beanstalk returns
            MissingRequiredParameter error.

        :type terminate_resources: boolean
        :param terminate_resources: Indicates whether the associated AWS
            resources should shut down when the environment is terminated:
            true: (default) The user AWS resources (for example, the Auto
            Scaling group, LoadBalancer, etc.) are terminated along with the
            environment.  false: The environment is removed from the AWS
            Elastic Beanstalk but the AWS resources continue to operate.  For
            more information, see the  AWS Elastic Beanstalk User Guide.
            Default: true  Valid Values: true | false

        :raises: InsufficientPrivilegesException
        """
        params = {}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        if terminate_resources:
            params['TerminateResources'] = self._encode_bool(
                terminate_resources)
        return self._get_response('TerminateEnvironment', params)

    def update_application(self, application_name, description=None):
        """
        Updates the specified application to have the specified
        properties.

        :type application_name: string
        :param application_name: The name of the application to update.
            If no such application is found, UpdateApplication returns an
            InvalidParameterValue error.

        :type description: string
        :param description: A new description for the application.  Default: If
            not specified, AWS Elastic Beanstalk does not update the
            description.
        """
        params = {'ApplicationName': application_name}
        if description:
            params['Description'] = description
        return self._get_response('UpdateApplication', params)

    def update_application_version(self, application_name, version_label,
                                   description=None):
        """Updates the application version to have the properties.

        :type application_name: string
        :param application_name: The name of the application associated with
            this version.  If no application is found with this name,
            UpdateApplication returns an InvalidParameterValue error.

        :type version_label: string
        :param version_label: The name of the version to update. If no
            application version is found with this label, UpdateApplication
            returns an InvalidParameterValue error.

        :type description: string
        :param description: A new description for this release.
        """
        params = {'ApplicationName': application_name,
                  'VersionLabel': version_label}
        if description:
            params['Description'] = description
        return self._get_response('UpdateApplicationVersion', params)

    def update_configuration_template(self, application_name, template_name,
                                      description=None, option_settings=None,
                                      options_to_remove=None):
        """
        Updates the specified configuration template to have the
        specified properties or configuration option values.

        :type application_name: string
        :param application_name: The name of the application associated with
            the configuration template to update. If no application is found
            with this name, UpdateConfigurationTemplate returns an
            InvalidParameterValue error.

        :type template_name: string
        :param template_name: The name of the configuration template to update.
            If no configuration template is found with this name,
            UpdateConfigurationTemplate returns an InvalidParameterValue error.

        :type description: string
        :param description: A new description for the configuration.

        :type option_settings: list
        :param option_settings: A list of configuration option settings to
            update with the new specified option value.

        :type options_to_remove: list
        :param options_to_remove: A list of configuration options to remove
            from the configuration set.  Constraint: You can remove only
            UserDefined configuration options.

        :raises: InsufficientPrivilegesException
        """
        params = {'ApplicationName': application_name,
                  'TemplateName': template_name}
        if description:
            params['Description'] = description
        if option_settings:
            self._build_list_params(params, option_settings,
                                   'OptionSettings.member',
                                   ('Namespace', 'OptionName', 'Value'))
        if options_to_remove:
            self.build_list_params(params, options_to_remove,
                                   'OptionsToRemove.member')
        return self._get_response('UpdateConfigurationTemplate', params)

    def update_environment(self, environment_id=None, environment_name=None,
                           version_label=None, template_name=None,
                           description=None, option_settings=None,
                           options_to_remove=None, tier_name=None,
                           tier_type=None, tier_version='1.0'):
        """
        Updates the environment description, deploys a new application
        version, updates the configuration settings to an entirely new
        configuration template, or updates select configuration option
        values in the running environment.  Attempting to update both
        the release and configuration is not allowed and AWS Elastic
        Beanstalk returns an InvalidParameterCombination error.  When
        updating the configuration settings to a new template or
        individual settings, a draft configuration is created and
        DescribeConfigurationSettings for this environment returns two
        setting descriptions with different DeploymentStatus values.

        :type environment_id: string
        :param environment_id: The ID of the environment to update. If no
            environment with this ID exists, AWS Elastic Beanstalk returns an
            InvalidParameterValue error.  Condition: You must specify either
            this or an EnvironmentName, or both. If you do not specify either,
            AWS Elastic Beanstalk returns MissingRequiredParameter error.

        :type environment_name: string
        :param environment_name: The name of the environment to update.  If no
            environment with this name exists, AWS Elastic Beanstalk returns an
            InvalidParameterValue error.  Condition: You must specify either
            this or an EnvironmentId, or both. If you do not specify either,
            AWS Elastic Beanstalk returns MissingRequiredParameter error.

        :type version_label: string
        :param version_label: If this parameter is specified, AWS Elastic
            Beanstalk deploys the named application version to the environment.
            If no such application version is found, returns an
            InvalidParameterValue error.

        :type template_name: string
        :param template_name: If this parameter is specified, AWS Elastic
            Beanstalk deploys this configuration template to the environment.
            If no such configuration template is found, AWS Elastic Beanstalk
            returns an InvalidParameterValue error.

        :type description: string
        :param description: If this parameter is specified, AWS Elastic
            Beanstalk updates the description of this environment.

        :type option_settings: list
        :param option_settings: If specified, AWS Elastic Beanstalk updates the
            configuration set associated with the running environment and sets
            the specified configuration options to the requested value.

        :type options_to_remove: list
        :param options_to_remove: A list of custom user-defined configuration
            options to remove from the configuration set for this environment.

        :type tier_name: string
        :param tier_name: The name of the tier.  Valid values are
            "WebServer" and "Worker". Defaults to "WebServer".
            The ``tier_name`` and a ``tier_type`` parameters are
            related and the values provided must be valid.
            The possible combinations are:

              * "WebServer" and "Standard" (the default)
              * "Worker" and "SQS/HTTP"

        :type tier_type: string
        :param tier_type: The type of the tier.  Valid values are
            "Standard" if ``tier_name`` is "WebServer" and "SQS/HTTP"
            if ``tier_name`` is "Worker". Defaults to "Standard".

        :type tier_version: string
        :type tier_version: The version of the tier.  Valid values
            currently are "1.0". Defaults to "1.0".

        :raises: InsufficientPrivilegesException
        """
        params = {}
        if environment_id:
            params['EnvironmentId'] = environment_id
        if environment_name:
            params['EnvironmentName'] = environment_name
        if version_label:
            params['VersionLabel'] = version_label
        if template_name:
            params['TemplateName'] = template_name
        if description:
            params['Description'] = description
        if option_settings:
            self._build_list_params(params, option_settings,
                                   'OptionSettings.member',
                                   ('Namespace', 'OptionName', 'Value'))
        if options_to_remove:
            self.build_list_params(params, options_to_remove,
                                   'OptionsToRemove.member')
        if tier_name and tier_type and tier_version:
            params['Tier.Name'] = tier_name
            params['Tier.Type'] = tier_type
            params['Tier.Version'] = tier_version
        return self._get_response('UpdateEnvironment', params)

    def validate_configuration_settings(self, application_name,
                                        option_settings, template_name=None,
                                        environment_name=None):
        """
        Takes a set of configuration settings and either a
        configuration template or environment, and determines whether
        those values are valid.  This action returns a list of messages
        indicating any errors or warnings associated with the selection
        of option values.

        :type application_name: string
        :param application_name: The name of the application that the
            configuration template or environment belongs to.

        :type template_name: string
        :param template_name: The name of the configuration template to
            validate the settings against.  Condition: You cannot specify both
            this and an environment name.

        :type environment_name: string
        :param environment_name: The name of the environment to validate the
            settings against.  Condition: You cannot specify both this and a
            configuration template name.

        :type option_settings: list
        :param option_settings: A list of the options and desired values to
            evaluate.

        :raises: InsufficientPrivilegesException
        """
        params = {'ApplicationName': application_name}
        self._build_list_params(params, option_settings,
                               'OptionSettings.member',
                               ('Namespace', 'OptionName', 'Value'))
        if template_name:
            params['TemplateName'] = template_name
        if environment_name:
            params['EnvironmentName'] = environment_name
        return self._get_response('ValidateConfigurationSettings', params)

    def _build_list_params(self, params, user_values, prefix, tuple_names):
        # For params such as the ConfigurationOptionSettings,
        # they can specify a list of tuples where each tuple maps to a specific
        # arg.  For example:
        # user_values = [('foo', 'bar', 'baz']
        # prefix=MyOption.member
        # tuple_names=('One', 'Two', 'Three')
        # would result in:
        # MyOption.member.1.One = foo
        # MyOption.member.1.Two = bar
        # MyOption.member.1.Three = baz
        for i, user_value in enumerate(user_values, 1):
            current_prefix = '%s.%s' % (prefix, i)
            for key, value in zip(tuple_names, user_value):
                full_key = '%s.%s' % (current_prefix, key)
                params[full_key] = value
