"""
Helper class for creating decision responses.
"""


class Layer1Decisions(object):
    """
    Use this object to build a list of decisions for a decision response.
    Each method call will add append a new decision.  Retrieve the list
    of decisions from the _data attribute.

    """
    def __init__(self):
        self._data = []

    def schedule_activity_task(self,
                               activity_id,
                               activity_type_name,
                               activity_type_version,
                               task_list=None,
                               control=None,
                               heartbeat_timeout=None,
                               schedule_to_close_timeout=None,
                               schedule_to_start_timeout=None,
                               start_to_close_timeout=None,
                               input=None):
        """
        Schedules an activity task.

        :type activity_id: string
        :param activity_id: The activityId of the type of the activity
            being scheduled.

        :type activity_type_name: string
        :param activity_type_name: The name of the type of the activity
            being scheduled.

        :type activity_type_version: string
        :param activity_type_version: The version of the type of the
            activity being scheduled.

        :type task_list: string
        :param task_list: If set, specifies the name of the task list in
            which to schedule the activity task. If not specified, the
            defaultTaskList registered with the activity type will be used.
            Note: a task list for this activity task must be specified either
            as a default for the activity type or through this field. If
            neither this field is set nor a default task list was specified
            at registration time then a fault will be returned.
        """
        o = {}
        o['decisionType'] = 'ScheduleActivityTask'
        attrs = o['scheduleActivityTaskDecisionAttributes'] = {}
        attrs['activityId'] = activity_id
        attrs['activityType'] = {
            'name': activity_type_name,
            'version': activity_type_version,
        }
        if task_list is not None:
            attrs['taskList'] = {'name': task_list}
        if control is not None:
            attrs['control'] = control
        if heartbeat_timeout is not None:
            attrs['heartbeatTimeout'] = heartbeat_timeout
        if schedule_to_close_timeout is not None:
            attrs['scheduleToCloseTimeout'] = schedule_to_close_timeout
        if schedule_to_start_timeout is not None:
            attrs['scheduleToStartTimeout'] = schedule_to_start_timeout
        if start_to_close_timeout is not None:
            attrs['startToCloseTimeout'] = start_to_close_timeout
        if input is not None:
            attrs['input'] = input
        self._data.append(o)

    def request_cancel_activity_task(self, activity_id):
        """
        Attempts to cancel a previously scheduled activity task. If
        the activity task was scheduled but has not been assigned to a
        worker, then it will be canceled. If the activity task was
        already assigned to a worker, then the worker will be informed
        that cancellation has been requested in the response to
        RecordActivityTaskHeartbeat.
        """
        o = {}
        o['decisionType'] = 'RequestCancelActivityTask'
        attrs = o['requestCancelActivityTaskDecisionAttributes'] = {}
        attrs['activityId'] = activity_id
        self._data.append(o)

    def record_marker(self, marker_name, details=None):
        """
        Records a MarkerRecorded event in the history. Markers can be
        used for adding custom information in the history for instance
        to let deciders know that they do not need to look at the
        history beyond the marker event.
        """
        o = {}
        o['decisionType'] = 'RecordMarker'
        attrs = o['recordMarkerDecisionAttributes'] = {}
        attrs['markerName'] = marker_name
        if details is not None:
            attrs['details'] = details
        self._data.append(o)

    def complete_workflow_execution(self, result=None):
        """
        Closes the workflow execution and records a WorkflowExecutionCompleted
        event in the history
        """
        o = {}
        o['decisionType'] = 'CompleteWorkflowExecution'
        attrs = o['completeWorkflowExecutionDecisionAttributes'] = {}
        if result is not None:
            attrs['result'] = result
        self._data.append(o)

    def fail_workflow_execution(self, reason=None, details=None):
        """
        Closes the workflow execution and records a
        WorkflowExecutionFailed event in the history.
        """
        o = {}
        o['decisionType'] = 'FailWorkflowExecution'
        attrs = o['failWorkflowExecutionDecisionAttributes'] = {}
        if reason is not None:
            attrs['reason'] = reason
        if details is not None:
            attrs['details'] = details
        self._data.append(o)

    def cancel_workflow_executions(self, details=None):
        """
        Closes the workflow execution and records a WorkflowExecutionCanceled
        event in the history.
        """
        o = {}
        o['decisionType'] = 'CancelWorkflowExecution'
        attrs = o['cancelWorkflowExecutionsDecisionAttributes'] = {}
        if details is not None:
            attrs['details'] = details
        self._data.append(o)

    def continue_as_new_workflow_execution(self,
                                           child_policy=None,
                                           execution_start_to_close_timeout=None,
                                           input=None,
                                           tag_list=None,
                                           task_list=None,
                                           start_to_close_timeout=None,
                                           workflow_type_version=None):
        """
        Closes the workflow execution and starts a new workflow execution of
        the same type using the same workflow id and a unique run Id. A
        WorkflowExecutionContinuedAsNew event is recorded in the history.
        """
        o = {}
        o['decisionType'] = 'ContinueAsNewWorkflowExecution'
        attrs = o['continueAsNewWorkflowExecutionDecisionAttributes'] = {}
        if child_policy is not None:
            attrs['childPolicy'] = child_policy
        if execution_start_to_close_timeout is not None:
            attrs['executionStartToCloseTimeout'] = execution_start_to_close_timeout
        if input is not None:
            attrs['input'] = input
        if tag_list is not None:
            attrs['tagList'] = tag_list
        if task_list is not None:
            attrs['taskList'] = {'name': task_list}
        if start_to_close_timeout is not None:
            attrs['taskStartToCloseTimeout'] = start_to_close_timeout
        if workflow_type_version is not None:
            attrs['workflowTypeVersion'] = workflow_type_version
        self._data.append(o)

    def start_timer(self,
                    start_to_fire_timeout,
                    timer_id,
                    control=None):
        """
        Starts a timer for this workflow execution and records a TimerStarted
        event in the history.  This timer will fire after the specified delay
        and record a TimerFired event.
        """
        o = {}
        o['decisionType'] = 'StartTimer'
        attrs = o['startTimerDecisionAttributes'] = {}
        attrs['startToFireTimeout'] = start_to_fire_timeout
        attrs['timerId'] = timer_id
        if control is not None:
            attrs['control'] = control
        self._data.append(o)

    def cancel_timer(self, timer_id):
        """
        Cancels a previously started timer and records a TimerCanceled
        event in the history.
        """
        o = {}
        o['decisionType'] = 'CancelTimer'
        attrs = o['cancelTimerDecisionAttributes'] = {}
        attrs['timerId'] = timer_id
        self._data.append(o)

    def signal_external_workflow_execution(self,
                                           workflow_id,
                                           signal_name,
                                           run_id=None,
                                           control=None,
                                           input=None):
        """
        Requests a signal to be delivered to the specified external workflow
        execution and records a SignalExternalWorkflowExecutionInitiated
        event in the history.
        """
        o = {}
        o['decisionType'] = 'SignalExternalWorkflowExecution'
        attrs = o['signalExternalWorkflowExecutionDecisionAttributes'] = {}
        attrs['workflowId'] = workflow_id
        attrs['signalName'] = signal_name
        if run_id is not None:
            attrs['runId'] = run_id
        if control is not None:
            attrs['control'] = control
        if input is not None:
            attrs['input'] = input
        self._data.append(o)

    def request_cancel_external_workflow_execution(self,
                                                   workflow_id,
                                                   control=None,
                                                   run_id=None):
        """
        Requests that a request be made to cancel the specified
        external workflow execution and records a
        RequestCancelExternalWorkflowExecutionInitiated event in the
        history.
        """
        o = {}
        o['decisionType'] = 'RequestCancelExternalWorkflowExecution'
        attrs = o['requestCancelExternalWorkflowExecutionDecisionAttributes'] = {}
        attrs['workflowId'] = workflow_id
        if control is not None:
            attrs['control'] = control
        if run_id is not None:
            attrs['runId'] = run_id
        self._data.append(o)

    def start_child_workflow_execution(self,
                                       workflow_type_name,
                                       workflow_type_version,
                                       workflow_id,
                                       child_policy=None,
                                       control=None,
                                       execution_start_to_close_timeout=None,
                                       input=None,
                                       tag_list=None,
                                       task_list=None,
                                       task_start_to_close_timeout=None):
        """
        Requests that a child workflow execution be started and
        records a StartChildWorkflowExecutionInitiated event in the
        history.  The child workflow execution is a separate workflow
        execution with its own history.
        """
        o = {}
        o['decisionType'] = 'StartChildWorkflowExecution'
        attrs = o['startChildWorkflowExecutionDecisionAttributes'] = {}
        attrs['workflowType'] = {
            'name': workflow_type_name,
            'version': workflow_type_version,
        }
        attrs['workflowId'] = workflow_id
        if child_policy is not None:
            attrs['childPolicy'] = child_policy
        if control is not None:
            attrs['control'] = control
        if execution_start_to_close_timeout is not None:
            attrs['executionStartToCloseTimeout'] = execution_start_to_close_timeout
        if input is not None:
            attrs['input'] = input
        if tag_list is not None:
            attrs['tagList'] = tag_list
        if task_list is not None:
            attrs['taskList'] = {'name': task_list}
        if task_start_to_close_timeout is not None:
            attrs['taskStartToCloseTimeout'] = task_start_to_close_timeout
        self._data.append(o)
