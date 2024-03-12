"""
Tests for Layer1 of Simple Workflow

"""
import time
import uuid
import json
import traceback

from boto.swf.layer1_decisions import Layer1Decisions

from tests.integration.swf.test_layer1 import SimpleWorkflowLayer1TestBase



class SwfL1WorkflowExecutionTest(SimpleWorkflowLayer1TestBase):
    """
    test a simple workflow execution
    """
    swf = True

    def run_decider(self):
        """
        run one iteration of a simple decision engine
        """
        # Poll for a decision task.
        tries = 0
        while True:
            dtask = self.conn.poll_for_decision_task(self._domain,
                self._task_list, reverse_order=True)
            if dtask.get('taskToken') is not None:
                # This means a real decision task has arrived.
                break
            time.sleep(2)
            tries += 1
            if tries > 10:
                # Give up if it's taking too long.  Probably
                # means something is broken somewhere else.
                assert False, 'no decision task occurred'

        # Get the most recent interesting event.
        ignorable = (
            'DecisionTaskScheduled',
            'DecisionTaskStarted',
            'DecisionTaskTimedOut',
        )
        event = None
        for tevent in dtask['events']:
            if tevent['eventType'] not in ignorable:
                event = tevent
                break

        # Construct the decision response.
        decisions = Layer1Decisions()
        if event['eventType'] == 'WorkflowExecutionStarted':
            activity_id = str(uuid.uuid1())
            decisions.schedule_activity_task(activity_id,
                self._activity_type_name, self._activity_type_version,
                task_list=self._task_list,
                input=event['workflowExecutionStartedEventAttributes']['input'])
        elif event['eventType'] == 'ActivityTaskCompleted':
            decisions.complete_workflow_execution(
                result=event['activityTaskCompletedEventAttributes']['result'])
        elif event['eventType'] == 'ActivityTaskFailed':
            decisions.fail_workflow_execution(
                reason=event['activityTaskFailedEventAttributes']['reason'],
                details=event['activityTaskFailedEventAttributes']['details'])
        else:
            decisions.fail_workflow_execution(
                reason='unhandled decision task type; %r' % (event['eventType'],))

        # Send the decision response.
        r = self.conn.respond_decision_task_completed(dtask['taskToken'],
                                                      decisions=decisions._data,
                                                      execution_context=None)
        assert r is None


    def run_worker(self):
        """
        run one iteration of a simple worker engine
        """
        # Poll for an activity task.
        tries = 0
        while True:
            atask = self.conn.poll_for_activity_task(self._domain,
                self._task_list, identity='test worker')
            if atask.get('activityId') is not None:
                # This means a real activity task has arrived.
                break
            time.sleep(2)
            tries += 1
            if tries > 10:
                # Give up if it's taking too long.  Probably
                # means something is broken somewhere else.
                assert False, 'no activity task occurred'
        # Do the work or catch a "work exception."
        reason = None
        try:
            result = json.dumps(sum(json.loads(atask['input'])))
        except:
            reason = 'an exception was raised'
            details = traceback.format_exc()
        if reason is None:
            r = self.conn.respond_activity_task_completed(
                atask['taskToken'], result)
        else:
            r = self.conn.respond_activity_task_failed(
                atask['taskToken'], reason=reason, details=details)
        assert r is None


    def test_workflow_execution(self):
        # Start a workflow execution whose activity task will succeed.
        workflow_id = 'wfid-%.2f' % (time.time(),)
        r = self.conn.start_workflow_execution(self._domain,
                                               workflow_id,
                                               self._workflow_type_name,
                                               self._workflow_type_version,
                                               execution_start_to_close_timeout='20',
                                               input='[600, 15]')
        # Need the run_id to lookup the execution history later.
        run_id = r['runId']

        # Move the workflow execution forward by having the
        # decider schedule an activity task.
        self.run_decider()

        # Run the worker to handle the scheduled activity task.
        self.run_worker()

        # Complete the workflow execution by having the
        # decider close it down.
        self.run_decider()

        # Check that the result was stored in the execution history.
        r = self.conn.get_workflow_execution_history(self._domain,
                                                     run_id, workflow_id,
                                                     reverse_order=True)['events'][0]
        result = r['workflowExecutionCompletedEventAttributes']['result']
        assert json.loads(result) == 615


    def test_failed_workflow_execution(self):
        # Start a workflow execution whose activity task will fail.
        workflow_id = 'wfid-%.2f' % (time.time(),)
        r = self.conn.start_workflow_execution(self._domain,
                                               workflow_id,
                                               self._workflow_type_name,
                                               self._workflow_type_version,
                                               execution_start_to_close_timeout='20',
                                               input='[600, "s"]')
        # Need the run_id to lookup the execution history later.
        run_id = r['runId']

        # Move the workflow execution forward by having the
        # decider schedule an activity task.
        self.run_decider()

        # Run the worker to handle the scheduled activity task.
        self.run_worker()

        # Complete the workflow execution by having the
        # decider close it down.
        self.run_decider()

        # Check that the failure was stored in the execution history.
        r = self.conn.get_workflow_execution_history(self._domain,
                                                     run_id, workflow_id,
                                                     reverse_order=True)['events'][0]
        reason = r['workflowExecutionFailedEventAttributes']['reason']
        assert reason == 'an exception was raised'

