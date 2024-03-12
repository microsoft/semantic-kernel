"""Object-oriented interface to SWF wrapping boto.swf.layer1.Layer1"""

import time
from functools import wraps
from boto.swf.layer1 import Layer1
from boto.swf.layer1_decisions import Layer1Decisions

DEFAULT_CREDENTIALS = {
    'aws_access_key_id': None,
    'aws_secret_access_key': None
}

def set_default_credentials(aws_access_key_id, aws_secret_access_key):
    """Set default credentials."""
    DEFAULT_CREDENTIALS.update({
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
    })

class SWFBase(object):

    name = None
    domain = None
    aws_access_key_id = None
    aws_secret_access_key = None
    region = None

    def __init__(self, **kwargs):
        # Set default credentials.
        for credkey in ('aws_access_key_id', 'aws_secret_access_key'):
            if DEFAULT_CREDENTIALS.get(credkey):
                setattr(self, credkey, DEFAULT_CREDENTIALS[credkey])
        # Override attributes with keyword args.
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

        self._swf = Layer1(self.aws_access_key_id,
                           self.aws_secret_access_key,
                           region=self.region)

    def __repr__(self):
        rep_str = str(self.name)
        if hasattr(self, 'version'):
            rep_str += '-' + str(getattr(self, 'version'))
        return '<%s %r at 0x%x>' % (self.__class__.__name__, rep_str, id(self))

class Domain(SWFBase):

    """Simple Workflow Domain."""

    description = None
    retention = 30
    @wraps(Layer1.describe_domain)
    def describe(self):
        """DescribeDomain."""
        return self._swf.describe_domain(self.name)

    @wraps(Layer1.deprecate_domain)
    def deprecate(self):
        """DeprecateDomain"""
        self._swf.deprecate_domain(self.name)

    @wraps(Layer1.register_domain)
    def register(self):
        """RegisterDomain."""
        self._swf.register_domain(self.name, str(self.retention), 
                                  self.description)

    @wraps(Layer1.list_activity_types)
    def activities(self, status='REGISTERED', **kwargs):
        """ListActivityTypes."""
        act_types = self._swf.list_activity_types(self.name, status, **kwargs)
        act_objects = []
        for act_args in act_types['typeInfos']:
            act_ident = act_args['activityType']
            del act_args['activityType']
            act_args.update(act_ident)
            act_args.update({
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key,
                'domain': self.name,
                'region': self.region,
            })
            act_objects.append(ActivityType(**act_args))
        return act_objects

    @wraps(Layer1.list_workflow_types)
    def workflows(self, status='REGISTERED', **kwargs):
        """ListWorkflowTypes."""
        wf_types = self._swf.list_workflow_types(self.name, status, **kwargs)
        wf_objects = []
        for wf_args in wf_types['typeInfos']:
            wf_ident = wf_args['workflowType']
            del wf_args['workflowType']
            wf_args.update(wf_ident)
            wf_args.update({
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key,
                'domain': self.name,
                'region': self.region,
            })
            
            wf_objects.append(WorkflowType(**wf_args))
        return wf_objects

    def executions(self, closed=False, **kwargs):
        """List list open/closed executions.

        For a full list of available parameters refer to
        :py:func:`boto.swf.layer1.Layer1.list_closed_workflow_executions` and
        :py:func:`boto.swf.layer1.Layer1.list_open_workflow_executions`
        """
        if closed:
            executions = self._swf.list_closed_workflow_executions(self.name,
                                                                   **kwargs)
        else:
            if 'oldest_date' not in kwargs:
                # Last 24 hours.
                kwargs['oldest_date'] = time.time() - (3600 * 24)
            executions = self._swf.list_open_workflow_executions(self.name, 
                                                                 **kwargs)
        exe_objects = []
        for exe_args in executions['executionInfos']:
            for nested_key in ('execution', 'workflowType'):
                nested_dict = exe_args[nested_key]
                del exe_args[nested_key]
                exe_args.update(nested_dict)
            
            exe_args.update({
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key,
                'domain': self.name,
                'region': self.region,
            })
            
            exe_objects.append(WorkflowExecution(**exe_args))
        return exe_objects

    @wraps(Layer1.count_pending_activity_tasks)
    def count_pending_activity_tasks(self, task_list):
        """CountPendingActivityTasks."""
        return self._swf.count_pending_activity_tasks(self.name, task_list)

    @wraps(Layer1.count_pending_decision_tasks)
    def count_pending_decision_tasks(self, task_list):
        """CountPendingDecisionTasks."""
        return self._swf.count_pending_decision_tasks(self.name, task_list)
 

class Actor(SWFBase):

    task_list = None
    last_tasktoken = None
    domain = None

    def run(self):
        """To be overloaded by subclasses."""
        raise NotImplementedError()

class ActivityWorker(Actor):

    """Base class for SimpleWorkflow activity workers."""

    @wraps(Layer1.respond_activity_task_canceled)
    def cancel(self, task_token=None, details=None):
        """RespondActivityTaskCanceled."""
        if task_token is None:
            task_token = self.last_tasktoken
        return self._swf.respond_activity_task_canceled(task_token, details)

    @wraps(Layer1.respond_activity_task_completed)
    def complete(self, task_token=None, result=None):
        """RespondActivityTaskCompleted."""
        if task_token is None:
            task_token = self.last_tasktoken
        return self._swf.respond_activity_task_completed(task_token, result)

    @wraps(Layer1.respond_activity_task_failed)
    def fail(self, task_token=None, details=None, reason=None):
        """RespondActivityTaskFailed."""
        if task_token is None:
            task_token = self.last_tasktoken
        return self._swf.respond_activity_task_failed(task_token, details,
                                                      reason)

    @wraps(Layer1.record_activity_task_heartbeat)
    def heartbeat(self, task_token=None, details=None):
        """RecordActivityTaskHeartbeat."""
        if task_token is None:
            task_token = self.last_tasktoken
        return self._swf.record_activity_task_heartbeat(task_token, details)

    @wraps(Layer1.poll_for_activity_task)
    def poll(self, **kwargs):
        """PollForActivityTask."""
        task_list = self.task_list
        if 'task_list' in kwargs:
            task_list = kwargs.get('task_list')
            del kwargs['task_list']
        task = self._swf.poll_for_activity_task(self.domain, task_list,
                                                **kwargs)
        self.last_tasktoken = task.get('taskToken')
        return task

class Decider(Actor):

    """Base class for SimpleWorkflow deciders."""

    @wraps(Layer1.respond_decision_task_completed)
    def complete(self, task_token=None, decisions=None, **kwargs):
        """RespondDecisionTaskCompleted."""
        if isinstance(decisions, Layer1Decisions):
            # Extract decision list from a Layer1Decisions instance.
            decisions = decisions._data
        if task_token is None:
            task_token = self.last_tasktoken
        return self._swf.respond_decision_task_completed(task_token, decisions,
                                                         **kwargs)

    @wraps(Layer1.poll_for_decision_task)
    def poll(self, **kwargs):
        """PollForDecisionTask."""
        task_list = self.task_list
        if 'task_list' in kwargs:
            task_list = kwargs.get('task_list')
            del kwargs['task_list']
        decision_task = self._swf.poll_for_decision_task(self.domain, task_list,
                                                  **kwargs)
        self.last_tasktoken = decision_task.get('taskToken')
        return decision_task

class WorkflowType(SWFBase):

    """A versioned workflow type."""

    version = None
    task_list = None
    child_policy = 'TERMINATE'

    @wraps(Layer1.describe_workflow_type)
    def describe(self):
        """DescribeWorkflowType."""
        return self._swf.describe_workflow_type(self.domain, self.name,
                                                self.version)
    @wraps(Layer1.register_workflow_type)
    def register(self, **kwargs):
        """RegisterWorkflowType."""
        args = {
            'default_execution_start_to_close_timeout': '3600',
            'default_task_start_to_close_timeout': '300',
            'default_child_policy': 'TERMINATE',
        }
        args.update(kwargs)
        self._swf.register_workflow_type(self.domain, self.name, self.version,
                                         **args)

    @wraps(Layer1.deprecate_workflow_type)
    def deprecate(self):
        """DeprecateWorkflowType."""
        self._swf.deprecate_workflow_type(self.domain, self.name, self.version)
    
    @wraps(Layer1.start_workflow_execution)
    def start(self, **kwargs):
        """StartWorkflowExecution."""
        if 'workflow_id' in kwargs:
            workflow_id = kwargs['workflow_id']
            del kwargs['workflow_id']
        else:
            workflow_id = '%s-%s-%i' % (self.name, self.version, time.time())

        for def_attr in ('task_list', 'child_policy'):
            kwargs[def_attr] = kwargs.get(def_attr, getattr(self, def_attr))
        run_id = self._swf.start_workflow_execution(self.domain, workflow_id, 
                                    self.name, self.version, **kwargs)['runId']
        return WorkflowExecution(name=self.name, version=self.version,
               runId=run_id, domain=self.domain, workflowId=workflow_id,
               aws_access_key_id=self.aws_access_key_id,
               aws_secret_access_key=self.aws_secret_access_key)

class WorkflowExecution(SWFBase):

    """An instance of a workflow."""

    workflowId = None
    runId = None

    @wraps(Layer1.signal_workflow_execution)
    def signal(self, signame, **kwargs):
        """SignalWorkflowExecution."""
        self._swf.signal_workflow_execution(self.domain, signame, 
                                            self.workflowId, **kwargs)

    @wraps(Layer1.terminate_workflow_execution)
    def terminate(self, **kwargs):
        """TerminateWorkflowExecution (p. 103)."""
        return self._swf.terminate_workflow_execution(self.domain, 
                                        self.workflowId, **kwargs)

    @wraps(Layer1.get_workflow_execution_history)
    def history(self, **kwargs):
        """GetWorkflowExecutionHistory."""
        return self._swf.get_workflow_execution_history(self.domain, self.runId,
                                            self.workflowId, **kwargs)['events']

    @wraps(Layer1.describe_workflow_execution)
    def describe(self):
        """DescribeWorkflowExecution."""
        return self._swf.describe_workflow_execution(self.domain, self.runId,
                                                             self.workflowId)

    @wraps(Layer1.request_cancel_workflow_execution)
    def request_cancel(self):
        """RequestCancelWorkflowExecution."""
        return self._swf.request_cancel_workflow_execution(self.domain,
                                                   self.workflowId, self.runId)


class ActivityType(SWFBase):

    """A versioned activity type."""

    version = None

    @wraps(Layer1.deprecate_activity_type)
    def deprecate(self):
        """DeprecateActivityType."""
        return self._swf.deprecate_activity_type(self.domain, self.name,
                                                 self.version)

    @wraps(Layer1.describe_activity_type)
    def describe(self):
        """DescribeActivityType."""
        return self._swf.describe_activity_type(self.domain, self.name,
                                                self.version)

    @wraps(Layer1.register_activity_type)
    def register(self, **kwargs):
        """RegisterActivityType."""
        args = {
            'default_task_heartbeat_timeout': '600',
            'default_task_schedule_to_close_timeout': '3900',
            'default_task_schedule_to_start_timeout': '300',
            'default_task_start_to_close_timeout': '3600',
        }
        args.update(kwargs)
        self._swf.register_activity_type(self.domain, self.name, self.version,
                                         **args)
