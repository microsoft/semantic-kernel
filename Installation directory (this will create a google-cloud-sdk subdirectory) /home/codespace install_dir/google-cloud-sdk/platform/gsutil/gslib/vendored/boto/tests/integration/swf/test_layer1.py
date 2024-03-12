"""
Tests for Layer1 of Simple Workflow

"""
import os
import unittest
import time

from boto.swf.layer1 import Layer1
from boto.swf import exceptions as swf_exceptions



# A standard AWS account is permitted a maximum of 100 of SWF domains,
# registered or deprecated.  Deleting deprecated domains on demand does
# not appear possible.  Therefore, these tests reuse a default or
# user-named testing domain.  This is named by the user via the environment
# variable BOTO_SWF_UNITTEST_DOMAIN, if available.  Otherwise the default
# testing domain is literally "boto-swf-unittest-domain".  Do not use
# the testing domain for other purposes.
BOTO_SWF_UNITTEST_DOMAIN = os.environ.get("BOTO_SWF_UNITTEST_DOMAIN",
                                          "boto-swf-unittest-domain")

# A standard domain can have a maxiumum of 10,000 workflow types and
# activity types, registered or deprecated.  Therefore, eventually any
# tests which register new workflow types or activity types would begin
# to fail with LimitExceeded.  Instead of generating new workflow types
# and activity types, these tests reuse the existing types.

# The consequence of the limits and inability to delete deprecated
# domains, workflow types, and activity types is that the tests in
# this module will not test for the three register actions:
#    * register_domain
#    * register_workflow_type
#    * register_activity_type
# Instead, the setUp of the TestCase create a domain, workflow type,
# and activity type, expecting that they may already exist, and the
# tests themselves test other things.

# If you really want to re-test the register_* functions in their
# ability to create things (rather than just reporting that they
# already exist), you'll need to use a new BOTO_SWF_UNITTEST_DOMAIN.
# But, beware that once you hit 100 domains, you are cannot create any
# more, delete existing ones, or rename existing ones.

# Some API calls establish resources, but these resources are not instantly
# available to the next API call.  For testing purposes, it is necessary to
# have a short pause to avoid having tests fail for invalid reasons.
PAUSE_SECONDS = 4



class SimpleWorkflowLayer1TestBase(unittest.TestCase):
    """
    There are at least two test cases which share this setUp/tearDown
    and the class-based parameter definitions:
        * SimpleWorkflowLayer1Test
        * tests.swf.test_layer1_workflow_execution.SwfL1WorkflowExecutionTest
    """
    swf = True
    # Some params used throughout the tests...
    # Domain registration params...
    _domain = BOTO_SWF_UNITTEST_DOMAIN
    _workflow_execution_retention_period_in_days = 'NONE'
    _domain_description = 'test workflow domain'
    # Type registration params used for workflow type and activity type...
    _task_list = 'tasklist1'
    # Workflow type registration params...
    _workflow_type_name = 'wft1'
    _workflow_type_version = '1'
    _workflow_type_description = 'wft1 description'
    _default_child_policy = 'REQUEST_CANCEL'
    _default_execution_start_to_close_timeout = '600'
    _default_task_start_to_close_timeout = '60'
    # Activity type registration params...
    _activity_type_name = 'at1'
    _activity_type_version = '1'
    _activity_type_description = 'at1 description'
    _default_task_heartbeat_timeout = '30'
    _default_task_schedule_to_close_timeout = '90'
    _default_task_schedule_to_start_timeout = '10'
    _default_task_start_to_close_timeout = '30'


    def setUp(self):
        # Create a Layer1 connection for testing.
        # Tester needs boto config or keys in environment variables.
        self.conn = Layer1()

        # Register a domain.  Expect None (success) or
        # SWFDomainAlreadyExistsError.
        try:
            r = self.conn.register_domain(self._domain,
                    self._workflow_execution_retention_period_in_days,
                    description=self._domain_description)
            assert r is None
            time.sleep(PAUSE_SECONDS)
        except swf_exceptions.SWFDomainAlreadyExistsError:
            pass

        # Register a workflow type.  Expect None (success) or
        # SWFTypeAlreadyExistsError.
        try:
            r = self.conn.register_workflow_type(self._domain,
                    self._workflow_type_name, self._workflow_type_version,
                    task_list=self._task_list,
                    default_child_policy=self._default_child_policy,
                    default_execution_start_to_close_timeout=
                        self._default_execution_start_to_close_timeout,
                    default_task_start_to_close_timeout=
                        self._default_task_start_to_close_timeout,
                    description=self._workflow_type_description)
            assert r is None
            time.sleep(PAUSE_SECONDS)
        except swf_exceptions.SWFTypeAlreadyExistsError:
            pass

        # Register an activity type.  Expect None (success) or
        # SWFTypeAlreadyExistsError.
        try:
            r = self.conn.register_activity_type(self._domain,
                    self._activity_type_name, self._activity_type_version,
                    task_list=self._task_list,
                    default_task_heartbeat_timeout=
                        self._default_task_heartbeat_timeout,
                    default_task_schedule_to_close_timeout=
                        self._default_task_schedule_to_close_timeout,
                    default_task_schedule_to_start_timeout=
                        self._default_task_schedule_to_start_timeout,
                    default_task_start_to_close_timeout=
                        self._default_task_start_to_close_timeout,
                    description=self._activity_type_description)
            assert r is None
            time.sleep(PAUSE_SECONDS)
        except swf_exceptions.SWFTypeAlreadyExistsError:
            pass

    def tearDown(self):
        # Delete what we can...
        pass




class SimpleWorkflowLayer1Test(SimpleWorkflowLayer1TestBase):

    def test_list_domains(self):
        # Find the domain.
        r = self.conn.list_domains('REGISTERED')
        found = None
        for info in r['domainInfos']:
            if info['name'] == self._domain:
                found = info
                break
        self.assertNotEqual(found, None, 'list_domains; test domain not found')
        # Validate some properties.
        self.assertEqual(found['description'], self._domain_description,
                         'list_domains; description does not match')
        self.assertEqual(found['status'], 'REGISTERED',
                         'list_domains; status does not match')

    def test_list_workflow_types(self):
        # Find the workflow type.
        r = self.conn.list_workflow_types(self._domain, 'REGISTERED')
        found = None
        for info in r['typeInfos']:
            if ( info['workflowType']['name'] == self._workflow_type_name and
                 info['workflowType']['version'] == self._workflow_type_version ):
                found = info
                break
        self.assertNotEqual(found, None, 'list_workflow_types; test type not found')
        # Validate some properties.
        self.assertEqual(found['description'], self._workflow_type_description,
                         'list_workflow_types; description does not match')
        self.assertEqual(found['status'], 'REGISTERED',
                         'list_workflow_types; status does not match')

    def test_list_activity_types(self):
        # Find the activity type.
        r = self.conn.list_activity_types(self._domain, 'REGISTERED')
        found = None
        for info in r['typeInfos']:
            if info['activityType']['name'] == self._activity_type_name:
                found = info
                break
        self.assertNotEqual(found, None, 'list_activity_types; test type not found')
        # Validate some properties.
        self.assertEqual(found['description'], self._activity_type_description,
                         'list_activity_types; description does not match')
        self.assertEqual(found['status'], 'REGISTERED',
                         'list_activity_types; status does not match')


    def test_list_closed_workflow_executions(self):
        # Test various legal ways to call function.
        latest_date = time.time()
        oldest_date = time.time() - 3600
        # With startTimeFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            start_latest_date=latest_date, start_oldest_date=oldest_date)
        # With closeTimeFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date)
        # With closeStatusFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date,
            close_status='COMPLETED')
        # With tagFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date,
            tag='ig')
        # With executionFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date,
            workflow_id='ig')
        # With typeFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date,
            workflow_name='ig', workflow_version='ig')
        # With reverseOrder...
        self.conn.list_closed_workflow_executions(self._domain, 
            close_latest_date=latest_date, close_oldest_date=oldest_date,
            reverse_order=True)


    def test_list_open_workflow_executions(self):
        # Test various legal ways to call function.
        latest_date = time.time()
        oldest_date = time.time() - 3600
        # With required params only...
        self.conn.list_closed_workflow_executions(self._domain, 
            latest_date, oldest_date)
        # With tagFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            latest_date, oldest_date, tag='ig')
        # With executionFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            latest_date, oldest_date, workflow_id='ig')
        # With typeFilter...
        self.conn.list_closed_workflow_executions(self._domain, 
            latest_date, oldest_date,
            workflow_name='ig', workflow_version='ig')
        # With reverseOrder...
        self.conn.list_closed_workflow_executions(self._domain, 
            latest_date, oldest_date, reverse_order=True)

