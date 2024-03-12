from tests.unit import unittest

import boto.swf.layer1_decisions


class TestDecisions(unittest.TestCase):

    def setUp(self):
        self.decisions = boto.swf.layer1_decisions.Layer1Decisions()

    def assert_data(self, *data):
        self.assertEquals(self.decisions._data, list(data))

    def test_continue_as_new_workflow_execution(self):
        self.decisions.continue_as_new_workflow_execution(
            child_policy='TERMINATE',
            execution_start_to_close_timeout='10',
            input='input',
            tag_list=['t1', 't2'],
            task_list='tasklist',
            start_to_close_timeout='20',
            workflow_type_version='v2'
        )
        self.assert_data({
            'decisionType': 'ContinueAsNewWorkflowExecution',
            'continueAsNewWorkflowExecutionDecisionAttributes': {
                'childPolicy': 'TERMINATE',
                'executionStartToCloseTimeout': '10',
                'input': 'input',
                'tagList': ['t1', 't2'],
                'taskList': {'name': 'tasklist'},
                'taskStartToCloseTimeout': '20',
                'workflowTypeVersion': 'v2',
            }
        })
