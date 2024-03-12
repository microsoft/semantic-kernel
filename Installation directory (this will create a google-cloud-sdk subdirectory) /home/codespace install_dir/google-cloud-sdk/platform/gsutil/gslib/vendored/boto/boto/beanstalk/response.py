"""Classify responses from layer1 and strict type values."""
from datetime import datetime
from boto.compat import six


class BaseObject(object):

    def __repr__(self):
        result = self.__class__.__name__ + '{ '
        counter = 0
        for key, value in six.iteritems(self.__dict__):
            # first iteration no comma
            counter += 1
            if counter > 1:
                result += ', '
            result += key + ': '
            result += self._repr_by_type(value)
        result += ' }'
        return result

    def _repr_by_type(self, value):
        # Everything is either a 'Response', 'list', or 'None/str/int/bool'.
        result = ''
        if isinstance(value, Response):
            result += value.__repr__()
        elif isinstance(value, list):
            result += self._repr_list(value)
        else:
            result += str(value)
        return result

    def _repr_list(self, array):
        result = '['
        for value in array:
            result += ' ' + self._repr_by_type(value) + ','
        # Check for trailing comma with a space.
        if len(result) > 1:
            result = result[:-1] + ' '
        result += ']'
        return result


class Response(BaseObject):
    def __init__(self, response):
        super(Response, self).__init__()

        if response['ResponseMetadata']:
            self.response_metadata = ResponseMetadata(response['ResponseMetadata'])
        else:
            self.response_metadata = None


class ResponseMetadata(BaseObject):
    def __init__(self, response):
        super(ResponseMetadata, self).__init__()

        self.request_id = str(response['RequestId'])


class ApplicationDescription(BaseObject):
    def __init__(self, response):
        super(ApplicationDescription, self).__init__()

        self.application_name = str(response['ApplicationName'])
        self.configuration_templates = []
        if response['ConfigurationTemplates']:
            for member in response['ConfigurationTemplates']:
                configuration_template = str(member)
                self.configuration_templates.append(configuration_template)
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        self.versions = []
        if response['Versions']:
            for member in response['Versions']:
                version = str(member)
                self.versions.append(version)


class ApplicationVersionDescription(BaseObject):
    def __init__(self, response):
        super(ApplicationVersionDescription, self).__init__()

        self.application_name = str(response['ApplicationName'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        if response['SourceBundle']:
            self.source_bundle = S3Location(response['SourceBundle'])
        else:
            self.source_bundle = None
        self.version_label = str(response['VersionLabel'])


class AutoScalingGroup(BaseObject):
    def __init__(self, response):
        super(AutoScalingGroup, self).__init__()

        self.name = str(response['Name'])


class ConfigurationOptionDescription(BaseObject):
    def __init__(self, response):
        super(ConfigurationOptionDescription, self).__init__()

        self.change_severity = str(response['ChangeSeverity'])
        self.default_value = str(response['DefaultValue'])
        self.max_length = int(response['MaxLength']) if response['MaxLength'] else None
        self.max_value = int(response['MaxValue']) if response['MaxValue'] else None
        self.min_value = int(response['MinValue']) if response['MinValue'] else None
        self.name = str(response['Name'])
        self.namespace = str(response['Namespace'])
        if response['Regex']:
            self.regex = OptionRestrictionRegex(response['Regex'])
        else:
            self.regex = None
        self.user_defined = str(response['UserDefined'])
        self.value_options = []
        if response['ValueOptions']:
            for member in response['ValueOptions']:
                value_option = str(member)
                self.value_options.append(value_option)
        self.value_type = str(response['ValueType'])


class ConfigurationOptionSetting(BaseObject):
    def __init__(self, response):
        super(ConfigurationOptionSetting, self).__init__()

        self.namespace = str(response['Namespace'])
        self.option_name = str(response['OptionName'])
        self.value = str(response['Value'])


class ConfigurationSettingsDescription(BaseObject):
    def __init__(self, response):
        super(ConfigurationSettingsDescription, self).__init__()

        self.application_name = str(response['ApplicationName'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.deployment_status = str(response['DeploymentStatus'])
        self.description = str(response['Description'])
        self.environment_name = str(response['EnvironmentName'])
        self.option_settings = []
        if response['OptionSettings']:
            for member in response['OptionSettings']:
                option_setting = ConfigurationOptionSetting(member)
                self.option_settings.append(option_setting)
        self.solution_stack_name = str(response['SolutionStackName'])
        self.template_name = str(response['TemplateName'])


class EnvironmentDescription(BaseObject):
    def __init__(self, response):
        super(EnvironmentDescription, self).__init__()

        self.application_name = str(response['ApplicationName'])
        self.cname = str(response['CNAME'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        self.endpoint_url = str(response['EndpointURL'])
        self.environment_id = str(response['EnvironmentId'])
        self.environment_name = str(response['EnvironmentName'])
        self.health = str(response['Health'])
        if response['Resources']:
            self.resources = EnvironmentResourcesDescription(response['Resources'])
        else:
            self.resources = None
        self.solution_stack_name = str(response['SolutionStackName'])
        self.status = str(response['Status'])
        self.template_name = str(response['TemplateName'])
        self.version_label = str(response['VersionLabel'])


class EnvironmentInfoDescription(BaseObject):
    def __init__(self, response):
        super(EnvironmentInfoDescription, self).__init__()

        self.ec2_instance_id = str(response['Ec2InstanceId'])
        self.info_type = str(response['InfoType'])
        self.message = str(response['Message'])
        self.sample_timestamp = datetime.fromtimestamp(response['SampleTimestamp'])


class EnvironmentResourceDescription(BaseObject):
    def __init__(self, response):
        super(EnvironmentResourceDescription, self).__init__()

        self.auto_scaling_groups = []
        if response['AutoScalingGroups']:
            for member in response['AutoScalingGroups']:
                auto_scaling_group = AutoScalingGroup(member)
                self.auto_scaling_groups.append(auto_scaling_group)
        self.environment_name = str(response['EnvironmentName'])
        self.instances = []
        if response['Instances']:
            for member in response['Instances']:
                instance = Instance(member)
                self.instances.append(instance)
        self.launch_configurations = []
        if response['LaunchConfigurations']:
            for member in response['LaunchConfigurations']:
                launch_configuration = LaunchConfiguration(member)
                self.launch_configurations.append(launch_configuration)
        self.load_balancers = []
        if response['LoadBalancers']:
            for member in response['LoadBalancers']:
                load_balancer = LoadBalancer(member)
                self.load_balancers.append(load_balancer)
        self.triggers = []
        if response['Triggers']:
            for member in response['Triggers']:
                trigger = Trigger(member)
                self.triggers.append(trigger)


class EnvironmentResourcesDescription(BaseObject):
    def __init__(self, response):
        super(EnvironmentResourcesDescription, self).__init__()

        if response['LoadBalancer']:
            self.load_balancer = LoadBalancerDescription(response['LoadBalancer'])
        else:
            self.load_balancer = None


class EventDescription(BaseObject):
    def __init__(self, response):
        super(EventDescription, self).__init__()

        self.application_name = str(response['ApplicationName'])
        self.environment_name = str(response['EnvironmentName'])
        self.event_date = datetime.fromtimestamp(response['EventDate'])
        self.message = str(response['Message'])
        self.request_id = str(response['RequestId'])
        self.severity = str(response['Severity'])
        self.template_name = str(response['TemplateName'])
        self.version_label = str(response['VersionLabel'])


class Instance(BaseObject):
    def __init__(self, response):
        super(Instance, self).__init__()

        self.id = str(response['Id'])


class LaunchConfiguration(BaseObject):
    def __init__(self, response):
        super(LaunchConfiguration, self).__init__()

        self.name = str(response['Name'])


class Listener(BaseObject):
    def __init__(self, response):
        super(Listener, self).__init__()

        self.port = int(response['Port']) if response['Port'] else None
        self.protocol = str(response['Protocol'])


class LoadBalancer(BaseObject):
    def __init__(self, response):
        super(LoadBalancer, self).__init__()

        self.name = str(response['Name'])


class LoadBalancerDescription(BaseObject):
    def __init__(self, response):
        super(LoadBalancerDescription, self).__init__()

        self.domain = str(response['Domain'])
        self.listeners = []
        if response['Listeners']:
            for member in response['Listeners']:
                listener = Listener(member)
                self.listeners.append(listener)
        self.load_balancer_name = str(response['LoadBalancerName'])


class OptionRestrictionRegex(BaseObject):
    def __init__(self, response):
        super(OptionRestrictionRegex, self).__init__()

        self.label = response['Label']
        self.pattern = response['Pattern']


class SolutionStackDescription(BaseObject):
    def __init__(self, response):
        super(SolutionStackDescription, self).__init__()

        self.permitted_file_types = []
        if response['PermittedFileTypes']:
            for member in response['PermittedFileTypes']:
                permitted_file_type = str(member)
                self.permitted_file_types.append(permitted_file_type)
        self.solution_stack_name = str(response['SolutionStackName'])


class S3Location(BaseObject):
    def __init__(self, response):
        super(S3Location, self).__init__()

        self.s3_bucket = str(response['S3Bucket'])
        self.s3_key = str(response['S3Key'])


class Trigger(BaseObject):
    def __init__(self, response):
        super(Trigger, self).__init__()

        self.name = str(response['Name'])


class ValidationMessage(BaseObject):
    def __init__(self, response):
        super(ValidationMessage, self).__init__()

        self.message = str(response['Message'])
        self.namespace = str(response['Namespace'])
        self.option_name = str(response['OptionName'])
        self.severity = str(response['Severity'])


# These are the response objects layer2 uses, one for each layer1 api call.
class CheckDNSAvailabilityResponse(Response):
    def __init__(self, response):
        response = response['CheckDNSAvailabilityResponse']
        super(CheckDNSAvailabilityResponse, self).__init__(response)

        response = response['CheckDNSAvailabilityResult']
        self.fully_qualified_cname = str(response['FullyQualifiedCNAME'])
        self.available = bool(response['Available'])


# Our naming convension produces this class name but api names it with more
# capitals.
class CheckDnsAvailabilityResponse(CheckDNSAvailabilityResponse): pass


class CreateApplicationResponse(Response):
    def __init__(self, response):
        response = response['CreateApplicationResponse']
        super(CreateApplicationResponse, self).__init__(response)

        response = response['CreateApplicationResult']
        if response['Application']:
            self.application = ApplicationDescription(response['Application'])
        else:
            self.application = None


class CreateApplicationVersionResponse(Response):
    def __init__(self, response):
        response = response['CreateApplicationVersionResponse']
        super(CreateApplicationVersionResponse, self).__init__(response)

        response = response['CreateApplicationVersionResult']
        if response['ApplicationVersion']:
            self.application_version = ApplicationVersionDescription(response['ApplicationVersion'])
        else:
            self.application_version = None


class CreateConfigurationTemplateResponse(Response):
    def __init__(self, response):
        response = response['CreateConfigurationTemplateResponse']
        super(CreateConfigurationTemplateResponse, self).__init__(response)

        response = response['CreateConfigurationTemplateResult']
        self.application_name = str(response['ApplicationName'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.deployment_status = str(response['DeploymentStatus'])
        self.description = str(response['Description'])
        self.environment_name = str(response['EnvironmentName'])
        self.option_settings = []
        if response['OptionSettings']:
            for member in response['OptionSettings']:
                option_setting = ConfigurationOptionSetting(member)
                self.option_settings.append(option_setting)
        self.solution_stack_name = str(response['SolutionStackName'])
        self.template_name = str(response['TemplateName'])


class CreateEnvironmentResponse(Response):
    def __init__(self, response):
        response = response['CreateEnvironmentResponse']
        super(CreateEnvironmentResponse, self).__init__(response)

        response = response['CreateEnvironmentResult']
        self.application_name = str(response['ApplicationName'])
        self.cname = str(response['CNAME'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        self.endpoint_url = str(response['EndpointURL'])
        self.environment_id = str(response['EnvironmentId'])
        self.environment_name = str(response['EnvironmentName'])
        self.health = str(response['Health'])
        if response['Resources']:
            self.resources = EnvironmentResourcesDescription(response['Resources'])
        else:
            self.resources = None
        self.solution_stack_name = str(response['SolutionStackName'])
        self.status = str(response['Status'])
        self.template_name = str(response['TemplateName'])
        self.version_label = str(response['VersionLabel'])


class CreateStorageLocationResponse(Response):
    def __init__(self, response):
        response = response['CreateStorageLocationResponse']
        super(CreateStorageLocationResponse, self).__init__(response)

        response = response['CreateStorageLocationResult']
        self.s3_bucket = str(response['S3Bucket'])


class DeleteApplicationResponse(Response):
    def __init__(self, response):
        response = response['DeleteApplicationResponse']
        super(DeleteApplicationResponse, self).__init__(response)


class DeleteApplicationVersionResponse(Response):
    def __init__(self, response):
        response = response['DeleteApplicationVersionResponse']
        super(DeleteApplicationVersionResponse, self).__init__(response)


class DeleteConfigurationTemplateResponse(Response):
    def __init__(self, response):
        response = response['DeleteConfigurationTemplateResponse']
        super(DeleteConfigurationTemplateResponse, self).__init__(response)


class DeleteEnvironmentConfigurationResponse(Response):
    def __init__(self, response):
        response = response['DeleteEnvironmentConfigurationResponse']
        super(DeleteEnvironmentConfigurationResponse, self).__init__(response)


class DescribeApplicationVersionsResponse(Response):
    def __init__(self, response):
        response = response['DescribeApplicationVersionsResponse']
        super(DescribeApplicationVersionsResponse, self).__init__(response)

        response = response['DescribeApplicationVersionsResult']
        self.application_versions = []
        if response['ApplicationVersions']:
            for member in response['ApplicationVersions']:
                application_version = ApplicationVersionDescription(member)
                self.application_versions.append(application_version)


class DescribeApplicationsResponse(Response):
    def __init__(self, response):
        response = response['DescribeApplicationsResponse']
        super(DescribeApplicationsResponse, self).__init__(response)

        response = response['DescribeApplicationsResult']
        self.applications = []
        if response['Applications']:
            for member in response['Applications']:
                application = ApplicationDescription(member)
                self.applications.append(application)


class DescribeConfigurationOptionsResponse(Response):
    def __init__(self, response):
        response = response['DescribeConfigurationOptionsResponse']
        super(DescribeConfigurationOptionsResponse, self).__init__(response)

        response = response['DescribeConfigurationOptionsResult']
        self.options = []
        if response['Options']:
            for member in response['Options']:
                option = ConfigurationOptionDescription(member)
                self.options.append(option)
        self.solution_stack_name = str(response['SolutionStackName'])


class DescribeConfigurationSettingsResponse(Response):
    def __init__(self, response):
        response = response['DescribeConfigurationSettingsResponse']
        super(DescribeConfigurationSettingsResponse, self).__init__(response)

        response = response['DescribeConfigurationSettingsResult']
        self.configuration_settings = []
        if response['ConfigurationSettings']:
            for member in response['ConfigurationSettings']:
                configuration_setting = ConfigurationSettingsDescription(member)
                self.configuration_settings.append(configuration_setting)


class DescribeEnvironmentResourcesResponse(Response):
    def __init__(self, response):
        response = response['DescribeEnvironmentResourcesResponse']
        super(DescribeEnvironmentResourcesResponse, self).__init__(response)

        response = response['DescribeEnvironmentResourcesResult']
        if response['EnvironmentResources']:
            self.environment_resources = EnvironmentResourceDescription(response['EnvironmentResources'])
        else:
            self.environment_resources = None


class DescribeEnvironmentsResponse(Response):
    def __init__(self, response):
        response = response['DescribeEnvironmentsResponse']
        super(DescribeEnvironmentsResponse, self).__init__(response)

        response = response['DescribeEnvironmentsResult']
        self.environments = []
        if response['Environments']:
            for member in response['Environments']:
                environment = EnvironmentDescription(member)
                self.environments.append(environment)


class DescribeEventsResponse(Response):
    def __init__(self, response):
        response = response['DescribeEventsResponse']
        super(DescribeEventsResponse, self).__init__(response)

        response = response['DescribeEventsResult']
        self.events = []
        if response['Events']:
            for member in response['Events']:
                event = EventDescription(member)
                self.events.append(event)
        self.next_tokent = str(response['NextToken'])


class ListAvailableSolutionStacksResponse(Response):
    def __init__(self, response):
        response = response['ListAvailableSolutionStacksResponse']
        super(ListAvailableSolutionStacksResponse, self).__init__(response)

        response = response['ListAvailableSolutionStacksResult']
        self.solution_stack_details = []
        if response['SolutionStackDetails']:
            for member in response['SolutionStackDetails']:
                solution_stack_detail = SolutionStackDescription(member)
                self.solution_stack_details.append(solution_stack_detail)
        self.solution_stacks = []
        if response['SolutionStacks']:
            for member in response['SolutionStacks']:
                solution_stack = str(member)
                self.solution_stacks.append(solution_stack)


class RebuildEnvironmentResponse(Response):
    def __init__(self, response):
        response = response['RebuildEnvironmentResponse']
        super(RebuildEnvironmentResponse, self).__init__(response)


class RequestEnvironmentInfoResponse(Response):
    def __init__(self, response):
        response = response['RequestEnvironmentInfoResponse']
        super(RequestEnvironmentInfoResponse, self).__init__(response)


class RestartAppServerResponse(Response):
    def __init__(self, response):
        response = response['RestartAppServerResponse']
        super(RestartAppServerResponse, self).__init__(response)


class RetrieveEnvironmentInfoResponse(Response):
    def __init__(self, response):
        response = response['RetrieveEnvironmentInfoResponse']
        super(RetrieveEnvironmentInfoResponse, self).__init__(response)

        response = response['RetrieveEnvironmentInfoResult']
        self.environment_info = []
        if response['EnvironmentInfo']:
            for member in response['EnvironmentInfo']:
                environment_info = EnvironmentInfoDescription(member)
                self.environment_info.append(environment_info)


class SwapEnvironmentCNAMEsResponse(Response):
    def __init__(self, response):
        response = response['SwapEnvironmentCNAMEsResponse']
        super(SwapEnvironmentCNAMEsResponse, self).__init__(response)


class SwapEnvironmentCnamesResponse(SwapEnvironmentCNAMEsResponse): pass


class TerminateEnvironmentResponse(Response):
    def __init__(self, response):
        response = response['TerminateEnvironmentResponse']
        super(TerminateEnvironmentResponse, self).__init__(response)

        response = response['TerminateEnvironmentResult']
        self.application_name = str(response['ApplicationName'])
        self.cname = str(response['CNAME'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        self.endpoint_url = str(response['EndpointURL'])
        self.environment_id = str(response['EnvironmentId'])
        self.environment_name = str(response['EnvironmentName'])
        self.health = str(response['Health'])
        if response['Resources']:
            self.resources = EnvironmentResourcesDescription(response['Resources'])
        else:
            self.resources = None
        self.solution_stack_name = str(response['SolutionStackName'])
        self.status = str(response['Status'])
        self.template_name = str(response['TemplateName'])
        self.version_label = str(response['VersionLabel'])


class UpdateApplicationResponse(Response):
    def __init__(self, response):
        response = response['UpdateApplicationResponse']
        super(UpdateApplicationResponse, self).__init__(response)

        response = response['UpdateApplicationResult']
        if response['Application']:
            self.application = ApplicationDescription(response['Application'])
        else:
            self.application = None


class UpdateApplicationVersionResponse(Response):
    def __init__(self, response):
        response = response['UpdateApplicationVersionResponse']
        super(UpdateApplicationVersionResponse, self).__init__(response)

        response = response['UpdateApplicationVersionResult']
        if response['ApplicationVersion']:
            self.application_version = ApplicationVersionDescription(response['ApplicationVersion'])
        else:
            self.application_version = None


class UpdateConfigurationTemplateResponse(Response):
    def __init__(self, response):
        response = response['UpdateConfigurationTemplateResponse']
        super(UpdateConfigurationTemplateResponse, self).__init__(response)

        response = response['UpdateConfigurationTemplateResult']
        self.application_name = str(response['ApplicationName'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.deployment_status = str(response['DeploymentStatus'])
        self.description = str(response['Description'])
        self.environment_name = str(response['EnvironmentName'])
        self.option_settings = []
        if response['OptionSettings']:
            for member in response['OptionSettings']:
                option_setting = ConfigurationOptionSetting(member)
                self.option_settings.append(option_setting)
        self.solution_stack_name = str(response['SolutionStackName'])
        self.template_name = str(response['TemplateName'])


class UpdateEnvironmentResponse(Response):
    def __init__(self, response):
        response = response['UpdateEnvironmentResponse']
        super(UpdateEnvironmentResponse, self).__init__(response)

        response = response['UpdateEnvironmentResult']
        self.application_name = str(response['ApplicationName'])
        self.cname = str(response['CNAME'])
        self.date_created = datetime.fromtimestamp(response['DateCreated'])
        self.date_updated = datetime.fromtimestamp(response['DateUpdated'])
        self.description = str(response['Description'])
        self.endpoint_url = str(response['EndpointURL'])
        self.environment_id = str(response['EnvironmentId'])
        self.environment_name = str(response['EnvironmentName'])
        self.health = str(response['Health'])
        if response['Resources']:
            self.resources = EnvironmentResourcesDescription(response['Resources'])
        else:
            self.resources = None
        self.solution_stack_name = str(response['SolutionStackName'])
        self.status = str(response['Status'])
        self.template_name = str(response['TemplateName'])
        self.version_label = str(response['VersionLabel'])


class ValidateConfigurationSettingsResponse(Response):
    def __init__(self, response):
        response = response['ValidateConfigurationSettingsResponse']
        super(ValidateConfigurationSettingsResponse, self).__init__(response)

        response = response['ValidateConfigurationSettingsResult']
        self.messages = []
        if response['Messages']:
            for member in response['Messages']:
                message = ValidationMessage(member)
                self.messages.append(message)
