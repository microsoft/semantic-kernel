#!/usr/bin/env python

import json

from tests.unit import AWSMockServiceTestCase

from boto.beanstalk.layer1 import Layer1

# These tests are just checking the basic structure of
# the Elastic Beanstalk code, by picking a few calls
# and verifying we get the expected results with mocked
# responses.  The integration tests actually verify the
# API calls interact with the service correctly.
class TestListAvailableSolutionStacks(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return json.dumps(
            {u'ListAvailableSolutionStacksResponse':
               {u'ListAvailableSolutionStacksResult':
                  {u'SolutionStackDetails': [
                      {u'PermittedFileTypes': [u'war', u'zip'],
                       u'SolutionStackName': u'32bit Amazon Linux running Tomcat 7'},
                      {u'PermittedFileTypes': [u'zip'],
                       u'SolutionStackName': u'32bit Amazon Linux running PHP 5.3'}],
                      u'SolutionStacks': [u'32bit Amazon Linux running Tomcat 7',
                                          u'32bit Amazon Linux running PHP 5.3']},
                u'ResponseMetadata': {u'RequestId': u'request_id'}}}).encode('utf-8')

    def test_list_available_solution_stacks(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.list_available_solution_stacks()
        stack_details = api_response['ListAvailableSolutionStacksResponse']\
                                    ['ListAvailableSolutionStacksResult']\
                                    ['SolutionStackDetails']
        solution_stacks = api_response['ListAvailableSolutionStacksResponse']\
                                      ['ListAvailableSolutionStacksResult']\
                                      ['SolutionStacks']
        self.assertEqual(solution_stacks,
                        [u'32bit Amazon Linux running Tomcat 7',
                         u'32bit Amazon Linux running PHP 5.3'])
        # These are the parameters that are actually sent to the CloudFormation
        # service.
        self.assert_request_parameters({
            'Action': 'ListAvailableSolutionStacks',
            'ContentType': 'JSON',
            'Version': '2010-12-01',
        })


class TestCreateApplicationVersion(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return json.dumps({
            'CreateApplicationVersionResponse':
              {u'CreateApplicationVersionResult':
                 {u'ApplicationVersion':
                    {u'ApplicationName': u'application1',
                     u'DateCreated': 1343067094.342,
                     u'DateUpdated': 1343067094.342,
                     u'Description': None,
                     u'SourceBundle': {u'S3Bucket': u'elasticbeanstalk-us-east-1',
                     u'S3Key': u'resources/elasticbeanstalk-sampleapp.war'},
                     u'VersionLabel': u'version1'}}}}).encode('utf-8')

    def test_create_application_version(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_application_version(
            'application1', 'version1', s3_bucket='mybucket', s3_key='mykey',
            auto_create_application=True)
        app_version = api_response['CreateApplicationVersionResponse']\
                                  ['CreateApplicationVersionResult']\
                                  ['ApplicationVersion']
        self.assert_request_parameters({
            'Action': 'CreateApplicationVersion',
            'ContentType': 'JSON',
            'Version': '2010-12-01',
            'ApplicationName': 'application1',
            'AutoCreateApplication': 'true',
            'SourceBundle.S3Bucket': 'mybucket',
            'SourceBundle.S3Key': 'mykey',
            'VersionLabel': 'version1',
        })
        self.assertEqual(app_version['ApplicationName'], 'application1')
        self.assertEqual(app_version['VersionLabel'], 'version1')


class TestCreateEnvironment(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return json.dumps({}).encode('utf-8')

    def test_create_environment(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_environment(
            'application1', 'environment1', 'version1',
            '32bit Amazon Linux running Tomcat 7',
            option_settings=[
                ('aws:autoscaling:launchconfiguration', 'Ec2KeyName',
                 'mykeypair'),
                ('aws:elasticbeanstalk:application:environment', 'ENVVAR',
                 'VALUE1')])
        self.assert_request_parameters({
            'Action': 'CreateEnvironment',
            'ApplicationName': 'application1',
            'EnvironmentName': 'environment1',
            'TemplateName': '32bit Amazon Linux running Tomcat 7',
            'ContentType': 'JSON',
            'Version': '2010-12-01',
            'VersionLabel': 'version1',
            'OptionSettings.member.1.Namespace': 'aws:autoscaling:launchconfiguration',
            'OptionSettings.member.1.OptionName': 'Ec2KeyName',
            'OptionSettings.member.1.Value': 'mykeypair',
            'OptionSettings.member.2.Namespace': 'aws:elasticbeanstalk:application:environment',
            'OptionSettings.member.2.OptionName': 'ENVVAR',
            'OptionSettings.member.2.Value': 'VALUE1',
        })

    def test_create_environment_with_tier(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_environment(
            'application1', 'environment1', 'version1',
            '32bit Amazon Linux running Tomcat 7',
            option_settings=[
                ('aws:autoscaling:launchconfiguration', 'Ec2KeyName',
                 'mykeypair'),
                ('aws:elasticbeanstalk:application:environment', 'ENVVAR',
                 'VALUE1')],
            tier_name='Worker', tier_type='SQS/HTTP', tier_version='1.0')
        self.assert_request_parameters({
            'Action': 'CreateEnvironment',
            'ApplicationName': 'application1',
            'EnvironmentName': 'environment1',
            'TemplateName': '32bit Amazon Linux running Tomcat 7',
            'ContentType': 'JSON',
            'Version': '2010-12-01',
            'VersionLabel': 'version1',
            'OptionSettings.member.1.Namespace': 'aws:autoscaling:launchconfiguration',
            'OptionSettings.member.1.OptionName': 'Ec2KeyName',
            'OptionSettings.member.1.Value': 'mykeypair',
            'OptionSettings.member.2.Namespace': 'aws:elasticbeanstalk:application:environment',
            'OptionSettings.member.2.OptionName': 'ENVVAR',
            'OptionSettings.member.2.Value': 'VALUE1',
            'Tier.Name': 'Worker',
            'Tier.Type': 'SQS/HTTP',
            'Tier.Version': '1.0',
        })
