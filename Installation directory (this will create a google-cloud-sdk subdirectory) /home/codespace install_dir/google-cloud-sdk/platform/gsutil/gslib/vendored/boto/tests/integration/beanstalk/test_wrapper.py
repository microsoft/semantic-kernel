import random
import time
from functools import partial

from tests.compat import unittest
from boto.beanstalk.wrapper import Layer1Wrapper
import boto.beanstalk.response as response


class BasicSuite(unittest.TestCase):
    def setUp(self):
        self.random_id = str(random.randint(1, 1000000))
        self.app_name = 'app-' + self.random_id
        self.app_version = 'version-' + self.random_id
        self.template = 'template-' + self.random_id
        self.environment = 'environment-' + self.random_id
        self.beanstalk = Layer1Wrapper()


class MiscSuite(BasicSuite):
    def test_check_dns_availability(self):
        result = self.beanstalk.check_dns_availability('amazon')
        self.assertIsInstance(result, response.CheckDNSAvailabilityResponse,
                              'incorrect response object returned')
        self.assertFalse(result.available)


class TestApplicationObjects(BasicSuite):
    def create_application(self):
        # This method is used for any API calls that require an application
        # object.  This also adds a cleanup step to automatically delete the
        # app when the test is finished.  No assertions are performed
        # here.  If you want to validate create_application, don't use this
        # method.
        self.beanstalk.create_application(application_name=self.app_name)
        self.addCleanup(partial(self.beanstalk.delete_application,
                                application_name=self.app_name))

    def test_create_delete_application_version(self):
        # This will create an app, create an app version, delete the app
        # version, and delete the app.  For each API call we check that the
        # return type is what we expect and that a few attributes have the
        # correct values.
        app_result = self.beanstalk.create_application(application_name=self.app_name)
        self.assertIsInstance(app_result, response.CreateApplicationResponse)
        self.assertEqual(app_result.application.application_name, self.app_name)

        version_result = self.beanstalk.create_application_version(
            application_name=self.app_name, version_label=self.app_version)
        self.assertIsInstance(version_result, response.CreateApplicationVersionResponse)
        self.assertEqual(version_result.application_version.version_label,
                         self.app_version)
        result = self.beanstalk.delete_application_version(
            application_name=self.app_name, version_label=self.app_version)
        self.assertIsInstance(result, response.DeleteApplicationVersionResponse)
        result = self.beanstalk.delete_application(
            application_name=self.app_name
        )
        self.assertIsInstance(result, response.DeleteApplicationResponse)

    def test_create_configuration_template(self):
        self.create_application()
        result = self.beanstalk.create_configuration_template(
            application_name=self.app_name, template_name=self.template,
            solution_stack_name='32bit Amazon Linux running Tomcat 6')
        self.assertIsInstance(
            result, response.CreateConfigurationTemplateResponse)
        self.assertEqual(result.solution_stack_name,
                         '32bit Amazon Linux running Tomcat 6')

    def test_create_storage_location(self):
        result = self.beanstalk.create_storage_location()
        self.assertIsInstance(result, response.CreateStorageLocationResponse)

    def test_update_application(self):
        self.create_application()
        result = self.beanstalk.update_application(application_name=self.app_name)
        self.assertIsInstance(result, response.UpdateApplicationResponse)

    def test_update_application_version(self):
        self.create_application()
        self.beanstalk.create_application_version(
            application_name=self.app_name, version_label=self.app_version)
        result = self.beanstalk.update_application_version(
            application_name=self.app_name, version_label=self.app_version)
        self.assertIsInstance(
            result, response.UpdateApplicationVersionResponse)


class GetSuite(BasicSuite):
    def test_describe_applications(self):
        result = self.beanstalk.describe_applications()
        self.assertIsInstance(result, response.DescribeApplicationsResponse)

    def test_describe_application_versions(self):
        result = self.beanstalk.describe_application_versions()
        self.assertIsInstance(result,
                              response.DescribeApplicationVersionsResponse)


    def test_describe_configuration_options(self):
        result = self.beanstalk.describe_configuration_options()
        self.assertIsInstance(result,
                              response.DescribeConfigurationOptionsResponse)

    def test_12_describe_environments(self):
        result = self.beanstalk.describe_environments()
        self.assertIsInstance(
            result, response.DescribeEnvironmentsResponse)

    def test_14_describe_events(self):
        result = self.beanstalk.describe_events()
        self.assertIsInstance(result, response.DescribeEventsResponse)

    def test_15_list_available_solution_stacks(self):
        result = self.beanstalk.list_available_solution_stacks()
        self.assertIsInstance(
            result, response.ListAvailableSolutionStacksResponse)
        self.assertIn('32bit Amazon Linux running Tomcat 6',
                      result.solution_stacks)



class TestsWithEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.random_id = str(random.randint(1, 1000000))
        cls.app_name = 'app-' + cls.random_id
        cls.environment = 'environment-' + cls.random_id
        cls.template = 'template-' + cls.random_id

        cls.beanstalk = Layer1Wrapper()
        cls.beanstalk.create_application(application_name=cls.app_name)
        cls.beanstalk.create_configuration_template(
            application_name=cls.app_name, template_name=cls.template,
            solution_stack_name='32bit Amazon Linux running Tomcat 6')
        cls.app_version = 'version-' + cls.random_id
        cls.beanstalk.create_application_version(
            application_name=cls.app_name, version_label=cls.app_version)
        cls.beanstalk.create_environment(cls.app_name, cls.environment,
                                         template_name=cls.template)
        cls.wait_for_env(cls.environment)

    @classmethod
    def tearDownClass(cls):
        cls.beanstalk.delete_application(application_name=cls.app_name,
                                         terminate_env_by_force=True)
        cls.wait_for_env(cls.environment, 'Terminated')

    @classmethod
    def wait_for_env(cls, env_name, status='Ready'):
        while not cls.env_ready(env_name, status):
            time.sleep(15)

    @classmethod
    def env_ready(cls, env_name, desired_status):
        result = cls.beanstalk.describe_environments(
            application_name=cls.app_name, environment_names=env_name)
        status = result.environments[0].status
        return status == desired_status

    def test_describe_environment_resources(self):
        result = self.beanstalk.describe_environment_resources(
            environment_name=self.environment)
        self.assertIsInstance(
            result, response.DescribeEnvironmentResourcesResponse)

    def test_describe_configuration_settings(self):
        result = self.beanstalk.describe_configuration_settings(
            application_name=self.app_name, environment_name=self.environment)
        self.assertIsInstance(
            result, response.DescribeConfigurationSettingsResponse)

    def test_request_environment_info(self):
        result = self.beanstalk.request_environment_info(
            environment_name=self.environment, info_type='tail')
        self.assertIsInstance(result, response.RequestEnvironmentInfoResponse)
        self.wait_for_env(self.environment)
        result = self.beanstalk.retrieve_environment_info(
            environment_name=self.environment, info_type='tail')
        self.assertIsInstance(result, response.RetrieveEnvironmentInfoResponse)

    def test_rebuild_environment(self):
        result = self.beanstalk.rebuild_environment(
            environment_name=self.environment)
        self.assertIsInstance(result, response.RebuildEnvironmentResponse)
        self.wait_for_env(self.environment)

    def test_restart_app_server(self):
        result = self.beanstalk.restart_app_server(
            environment_name=self.environment)
        self.assertIsInstance(result, response.RestartAppServerResponse)
        self.wait_for_env(self.environment)

    def test_update_configuration_template(self):
        result = self.beanstalk.update_configuration_template(
            application_name=self.app_name, template_name=self.template)
        self.assertIsInstance(
            result, response.UpdateConfigurationTemplateResponse)

    def test_update_environment(self):
        result = self.beanstalk.update_environment(
            environment_name=self.environment)
        self.assertIsInstance(result, response.UpdateEnvironmentResponse)
        self.wait_for_env(self.environment)


if __name__ == '__main__':
    unittest.main()
