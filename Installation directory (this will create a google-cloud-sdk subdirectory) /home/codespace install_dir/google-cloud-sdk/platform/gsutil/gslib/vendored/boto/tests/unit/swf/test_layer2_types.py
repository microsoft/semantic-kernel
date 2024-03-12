import boto.swf.layer2
from boto.swf.layer2 import ActivityType, WorkflowType, WorkflowExecution
from tests.unit import unittest
from mock import Mock, ANY


class TestTypes(unittest.TestCase):

    def setUp(self):
        boto.swf.layer2.Layer1 = Mock()
    
    def test_workflow_type_register_defaults(self):
        wf_type = WorkflowType(name='name', domain='test', version='1')
        wf_type.register()

        wf_type._swf.register_workflow_type.assert_called_with('test', 'name', '1',
            default_execution_start_to_close_timeout=ANY,    
            default_task_start_to_close_timeout=ANY,
            default_child_policy=ANY
        )

    def test_activity_type_register_defaults(self):
        act_type = ActivityType(name='name', domain='test', version='1')
        act_type.register()

        act_type._swf.register_activity_type.assert_called_with('test', 'name', '1',
            default_task_heartbeat_timeout=ANY,    
            default_task_schedule_to_close_timeout=ANY,
            default_task_schedule_to_start_timeout=ANY,
            default_task_start_to_close_timeout=ANY
        )

    def test_workflow_type_start_execution(self):
        wf_type = WorkflowType(name='name', domain='test', version='1')
        run_id = '122aJcg6ic7MRAkjDRzLBsqU/R49qt5D0LPHycT/6ArN4='
        wf_type._swf.start_workflow_execution.return_value = {'runId': run_id}
        
        execution = wf_type.start(task_list='hello_world')

        self.assertIsInstance(execution, WorkflowExecution)
        self.assertEquals(wf_type.name, execution.name)
        self.assertEquals(wf_type.version, execution.version)
        self.assertEquals(run_id, execution.runId)

if __name__ == '__main__':
    unittest.main()
