import boto.swf.layer2
from boto.swf.layer2 import Domain, ActivityType, WorkflowType, WorkflowExecution
from tests.unit import unittest
from mock import Mock


class TestDomain(unittest.TestCase):

    def setUp(self):
        boto.swf.layer2.Layer1 = Mock()
        self.domain = Domain(name='test-domain', description='My test domain')
        self.domain.aws_access_key_id = 'inheritable access key'
        self.domain.aws_secret_access_key = 'inheritable secret key'
        self.domain.region = 'test-region'

    def test_domain_instantiation(self):
        self.assertEquals('test-domain', self.domain.name)
        self.assertEquals('My test domain', self.domain.description)

    def test_domain_list_activities(self):
        self.domain._swf.list_activity_types.return_value = {
            'typeInfos': [{'activityType': {'name': 'DeleteLocalFile',
                             'version': '1.0'},
            'creationDate': 1332853651.235,
            'status': 'REGISTERED'},
           {'activityType': {'name': 'DoUpdate', 'version': 'test'},
            'creationDate': 1333463734.528,
            'status': 'REGISTERED'},
           {'activityType': {'name': 'GrayscaleTransform',
                             'version': '1.0'},
            'creationDate': 1332853651.18,
            'status': 'REGISTERED'},
           {'activityType': {'name': 'S3Download', 'version': '1.0'},
            'creationDate': 1332853651.264,
            'status': 'REGISTERED'},
           {'activityType': {'name': 'S3Upload', 'version': '1.0'},
            'creationDate': 1332853651.314,
            'status': 'REGISTERED'},
           {'activityType': {'name': 'SepiaTransform', 'version': '1.1'},
            'creationDate': 1333373797.734,
            'status': 'REGISTERED'}]} 
    
        expected_names = ('DeleteLocalFile', 'GrayscaleTransform', 'S3Download', 
                          'S3Upload', 'SepiaTransform', 'DoUpdate')

        activity_types = self.domain.activities()
        self.assertEquals(6, len(activity_types))
        for activity_type in activity_types:
            self.assertIsInstance(activity_type, ActivityType)
            self.assertTrue(activity_type.name in expected_names)
            self.assertEquals(self.domain.region, activity_type.region)

    def test_domain_list_workflows(self):
        self.domain._swf.list_workflow_types.return_value = {
            'typeInfos': [{'creationDate': 1332853651.136,
                'description': 'Image processing sample workflow type',
                'status': 'REGISTERED',
                'workflowType': {'name': 'ProcessFile', 'version': '1.0'}},
               {'creationDate': 1333551719.89,
                'status': 'REGISTERED',
                'workflowType': {'name': 'test_workflow_name',
                                 'version': 'v1'}}]}
        expected_names = ('ProcessFile', 'test_workflow_name') 
        
        workflow_types = self.domain.workflows()
        self.assertEquals(2, len(workflow_types))
        for workflow_type in workflow_types:
            self.assertIsInstance(workflow_type, WorkflowType)
            self.assertTrue(workflow_type.name in expected_names)
            self.assertEquals(self.domain.aws_access_key_id, workflow_type.aws_access_key_id)
            self.assertEquals(self.domain.aws_secret_access_key, workflow_type.aws_secret_access_key)
            self.assertEquals(self.domain.name, workflow_type.domain)
            self.assertEquals(self.domain.region, workflow_type.region)

    def test_domain_list_executions(self):
        self.domain._swf.list_open_workflow_executions.return_value = {
            'executionInfos': [{'cancelRequested': False,
                     'execution': {'runId': '12OeDTyoD27TDaafViz/QIlCHrYzspZmDgj0coIfjm868=',
                                   'workflowId': 'ProcessFile-1.0-1378933928'},
                     'executionStatus': 'OPEN',
                     'startTimestamp': 1378933928.676,
                     'workflowType': {'name': 'ProcessFile',
                                      'version': '1.0'}},
                    {'cancelRequested': False,
                     'execution': {'runId': '12GwBkx4hH6t2yaIh8LYxy5HyCM6HcyhDKePJCg0/ciJk=',
                                   'workflowId': 'ProcessFile-1.0-1378933927'},
                     'executionStatus': 'OPEN',
                     'startTimestamp': 1378933927.919,
                     'workflowType': {'name': 'ProcessFile',
                                      'version': '1.0'}},
                    {'cancelRequested': False,
                     'execution': {'runId': '12oRG3vEWrQ7oYBV+Bqi33Fht+ZRCYTt+tOdn5kLVcwKI=',
                                   'workflowId': 'ProcessFile-1.0-1378933926'},
                     'executionStatus': 'OPEN',
                     'startTimestamp': 1378933927.04,
                     'workflowType': {'name': 'ProcessFile',
                                      'version': '1.0'}},
                    {'cancelRequested': False,
                     'execution': {'runId': '12qrdcpYmad2cjnqJcM4Njm3qrCGvmRFR1wwQEt+a2ako=',
                                   'workflowId': 'ProcessFile-1.0-1378933874'},
                     'executionStatus': 'OPEN',
                     'startTimestamp': 1378933874.956,
                     'workflowType': {'name': 'ProcessFile',
                                      'version': '1.0'}}]}

        executions = self.domain.executions()
        self.assertEquals(4, len(executions))
        for wf_execution in executions:
            self.assertIsInstance(wf_execution, WorkflowExecution)
            self.assertEquals(self.domain.aws_access_key_id, wf_execution.aws_access_key_id)
            self.assertEquals(self.domain.aws_secret_access_key, wf_execution.aws_secret_access_key)
            self.assertEquals(self.domain.name, wf_execution.domain)
            self.assertEquals(self.domain.region, wf_execution.region)

if __name__ == '__main__':
    unittest.main()
