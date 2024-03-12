# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import xml.sax
import datetime
import itertools

from boto import handler
from boto import config
from boto.mturk.price import Price
import boto.mturk.notification
from boto.connection import AWSQueryConnection
from boto.exception import EC2ResponseError
from boto.resultset import ResultSet
from boto.mturk.question import QuestionForm, ExternalQuestion, HTMLQuestion


class MTurkRequestError(EC2ResponseError):
    "Error for MTurk Requests"
    # todo: subclass from an abstract parent of EC2ResponseError


class MTurkConnection(AWSQueryConnection):

    APIVersion = '2014-08-15'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None,
                 host=None, debug=0,
                 https_connection_factory=None, security_token=None,
                 profile_name=None):
        if not host:
            if config.has_option('MTurk', 'sandbox') and config.get('MTurk', 'sandbox') == 'True':
                host = 'mechanicalturk.sandbox.amazonaws.com'
            else:
                host = 'mechanicalturk.amazonaws.com'
        self.debug = debug

        super(MTurkConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass, host, debug,
                                    https_connection_factory,
                                    security_token=security_token,
                                    profile_name=profile_name)

    def _required_auth_capability(self):
        return ['mturk']

    def get_account_balance(self):
        """
        """
        params = {}
        return self._process_request('GetAccountBalance', params,
                                     [('AvailableBalance', Price),
                                      ('OnHoldBalance', Price)])

    def register_hit_type(self, title, description, reward, duration,
                          keywords=None, approval_delay=None, qual_req=None):
        """
        Register a new HIT Type
        title, description are strings
        reward is a Price object
        duration can be a timedelta, or an object castable to an int
        """
        params = dict(
            Title=title,
            Description=description,
            AssignmentDurationInSeconds=self.duration_as_seconds(duration),
            )
        params.update(MTurkConnection.get_price_as_price(reward).get_as_params('Reward'))

        if keywords:
            params['Keywords'] = self.get_keywords_as_string(keywords)

        if approval_delay is not None:
            d = self.duration_as_seconds(approval_delay)
            params['AutoApprovalDelayInSeconds'] = d

        if qual_req is not None:
            params.update(qual_req.get_as_params())

        return self._process_request('RegisterHITType', params,
                                     [('HITTypeId', HITTypeId)])

    def set_email_notification(self, hit_type, email, event_types=None):
        """
        Performs a SetHITTypeNotification operation to set email
        notification for a specified HIT type
        """
        return self._set_notification(hit_type, 'Email', email,
                                      'SetHITTypeNotification', event_types)

    def set_rest_notification(self, hit_type, url, event_types=None):
        """
        Performs a SetHITTypeNotification operation to set REST notification
        for a specified HIT type
        """
        return self._set_notification(hit_type, 'REST', url,
                                      'SetHITTypeNotification', event_types)

    def set_sqs_notification(self, hit_type, queue_url, event_types=None):
        """
        Performs a SetHITTypeNotification operation so set SQS notification
        for a specified HIT type. Queue URL is of form:
        https://queue.amazonaws.com/<CUSTOMER_ID>/<QUEUE_NAME> and can be
        found when looking at the details for a Queue in the AWS Console
        """
        return self._set_notification(hit_type, "SQS", queue_url,
                                      'SetHITTypeNotification', event_types)

    def send_test_event_notification(self, hit_type, url,
                                     event_types=None,
                                     test_event_type='Ping'):
        """
        Performs a SendTestEventNotification operation with REST notification
        for a specified HIT type
        """
        return self._set_notification(hit_type, 'REST', url,
                                      'SendTestEventNotification',
                                      event_types, test_event_type)

    def _set_notification(self, hit_type, transport,
                          destination, request_type,
                          event_types=None, test_event_type=None):
        """
        Common operation to set notification or send a test event
        notification for a specified HIT type
        """
        params = {'HITTypeId': hit_type}

        # from the Developer Guide:
        # The 'Active' parameter is optional. If omitted, the active status of
        # the HIT type's notification specification is unchanged. All HIT types
        # begin with their notification specifications in the "inactive" status.
        notification_params = {'Destination': destination,
                               'Transport': transport,
                               'Version': boto.mturk.notification.NotificationMessage.NOTIFICATION_VERSION,
                               'Active': True,
                               }

        # add specific event types if required
        if event_types:
            self.build_list_params(notification_params, event_types,
                                   'EventType')

        # Set up dict of 'Notification.1.Transport' etc. values
        notification_rest_params = {}
        num = 1
        for key in notification_params:
            notification_rest_params['Notification.%d.%s' % (num, key)] = notification_params[key]

        # Update main params dict
        params.update(notification_rest_params)

        # If test notification, specify the notification type to be tested
        if test_event_type:
            params.update({'TestEventType': test_event_type})

        # Execute operation
        return self._process_request(request_type, params)

    def create_hit(self, hit_type=None, question=None, hit_layout=None,
                   lifetime=datetime.timedelta(days=7),
                   max_assignments=1,
                   title=None, description=None, keywords=None,
                   reward=None, duration=datetime.timedelta(days=7),
                   approval_delay=None, annotation=None,
                   questions=None, qualifications=None,
                   layout_params=None, response_groups=None):
        """
        Creates a new HIT.
        Returns a ResultSet
        See: http://docs.amazonwebservices.com/AWSMechTurk/2012-03-25/AWSMturkAPI/ApiReference_CreateHITOperation.html
        """

        # Handle basic required arguments and set up params dict
        params = {'LifetimeInSeconds':
                      self.duration_as_seconds(lifetime),
                  'MaxAssignments': max_assignments,
                 }

        # handle single or multiple questions or layouts
        neither = question is None and questions is None
        if hit_layout is None:
            both = question is not None and questions is not None
            if neither or both:
                raise ValueError("Must specify question (single Question instance) or questions (list or QuestionForm instance), but not both")
            if question:
                questions = [question]
            question_param = QuestionForm(questions)
            if isinstance(question, QuestionForm):
                question_param = question
            elif isinstance(question, ExternalQuestion):
                question_param = question
            elif isinstance(question, HTMLQuestion):
                question_param = question
            params['Question'] = question_param.get_as_xml()
        else:
            if not neither:
                raise ValueError("Must not specify question (single Question instance) or questions (list or QuestionForm instance) when specifying hit_layout")
            params['HITLayoutId'] = hit_layout
            if layout_params:
                params.update(layout_params.get_as_params())

        # if hit type specified then add it
        # else add the additional required parameters
        if hit_type:
            params['HITTypeId'] = hit_type
        else:
            # Handle keywords
            final_keywords = MTurkConnection.get_keywords_as_string(keywords)

            # Handle price argument
            final_price = MTurkConnection.get_price_as_price(reward)

            final_duration = self.duration_as_seconds(duration)

            additional_params = dict(
                Title=title,
                Description=description,
                Keywords=final_keywords,
                AssignmentDurationInSeconds=final_duration,
                )
            additional_params.update(final_price.get_as_params('Reward'))

            if approval_delay is not None:
                d = self.duration_as_seconds(approval_delay)
                additional_params['AutoApprovalDelayInSeconds'] = d

            # add these params to the others
            params.update(additional_params)

        # add the annotation if specified
        if annotation is not None:
            params['RequesterAnnotation'] = annotation

        # Add the Qualifications if specified
        if qualifications is not None:
            params.update(qualifications.get_as_params())

        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        # Submit
        return self._process_request('CreateHIT', params, [('HIT', HIT)])

    def change_hit_type_of_hit(self, hit_id, hit_type):
        """
        Change the HIT type of an existing HIT. Note that the reward associated
        with the new HIT type must match the reward of the current HIT type in
        order for the operation to be valid.

        :type hit_id: str
        :type hit_type: str
        """
        params = {'HITId': hit_id,
                  'HITTypeId': hit_type}

        return self._process_request('ChangeHITTypeOfHIT', params)

    def get_reviewable_hits(self, hit_type=None, status='Reviewable',
                            sort_by='Expiration', sort_direction='Ascending',
                            page_size=10, page_number=1):
        """
        Retrieve the HITs that have a status of Reviewable, or HITs that
        have a status of Reviewing, and that belong to the Requester
        calling the operation.
        """
        params = {'Status': status,
                  'SortProperty': sort_by,
                  'SortDirection': sort_direction,
                  'PageSize': page_size,
                  'PageNumber': page_number}

        # Handle optional hit_type argument
        if hit_type is not None:
            params.update({'HITTypeId': hit_type})

        return self._process_request('GetReviewableHITs', params,
                                     [('HIT', HIT)])

    @staticmethod
    def _get_pages(page_size, total_records):
        """
        Given a page size (records per page) and a total number of
        records, return the page numbers to be retrieved.
        """
        pages = total_records / page_size + bool(total_records % page_size)
        return list(range(1, pages + 1))

    def get_all_hits(self):
        """
        Return all of a Requester's HITs

        Despite what search_hits says, it does not return all hits, but
        instead returns a page of hits. This method will pull the hits
        from the server 100 at a time, but will yield the results
        iteratively, so subsequent requests are made on demand.
        """
        page_size = 100
        search_rs = self.search_hits(page_size=page_size)
        total_records = int(search_rs.TotalNumResults)
        get_page_hits = lambda page: self.search_hits(page_size=page_size, page_number=page)
        page_nums = self._get_pages(page_size, total_records)
        hit_sets = itertools.imap(get_page_hits, page_nums)
        return itertools.chain.from_iterable(hit_sets)

    def search_hits(self, sort_by='CreationTime', sort_direction='Ascending',
                    page_size=10, page_number=1, response_groups=None):
        """
        Return a page of a Requester's HITs, on behalf of the Requester.
        The operation returns HITs of any status, except for HITs that
        have been disposed with the DisposeHIT operation.
        Note:
        The SearchHITs operation does not accept any search parameters
        that filter the results.
        """
        params = {'SortProperty': sort_by,
                  'SortDirection': sort_direction,
                  'PageSize': page_size,
                  'PageNumber': page_number}
        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        return self._process_request('SearchHITs', params, [('HIT', HIT)])

    def get_assignment(self, assignment_id, response_groups=None):
        """
        Retrieves an assignment using the assignment's ID. Requesters can only
        retrieve their own assignments, and only assignments whose related HIT
        has not been disposed.

        The returned ResultSet will have the following attributes:

        Request
                This element is present only if the Request ResponseGroup
                is specified.
        Assignment
                The assignment. The response includes one Assignment object.
        HIT
                The HIT associated with this assignment. The response
                includes one HIT object.

        """

        params = {'AssignmentId': assignment_id}

        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        return self._process_request('GetAssignment', params,
                                     [('Assignment', Assignment),
                                      ('HIT', HIT)])

    def get_assignments(self, hit_id, status=None,
                            sort_by='SubmitTime', sort_direction='Ascending',
                            page_size=10, page_number=1, response_groups=None):
        """
        Retrieves completed assignments for a HIT.
        Use this operation to retrieve the results for a HIT.

        The returned ResultSet will have the following attributes:

        NumResults
                The number of assignments on the page in the filtered results
                list, equivalent to the number of assignments being returned
                by this call.
                A non-negative integer, as a string.
        PageNumber
                The number of the page in the filtered results list being
                returned.
                A positive integer, as a string.
        TotalNumResults
                The total number of HITs in the filtered results list based
                on this call.
                A non-negative integer, as a string.

        The ResultSet will contain zero or more Assignment objects

        """
        params = {'HITId': hit_id,
                  'SortProperty': sort_by,
                  'SortDirection': sort_direction,
                  'PageSize': page_size,
                  'PageNumber': page_number}

        if status is not None:
            params['AssignmentStatus'] = status

        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        return self._process_request('GetAssignmentsForHIT', params,
                                     [('Assignment', Assignment)])

    def approve_assignment(self, assignment_id, feedback=None):
        """
        """
        params = {'AssignmentId': assignment_id}
        if feedback:
            params['RequesterFeedback'] = feedback
        return self._process_request('ApproveAssignment', params)

    def reject_assignment(self, assignment_id, feedback=None):
        """
        """
        params = {'AssignmentId': assignment_id}
        if feedback:
            params['RequesterFeedback'] = feedback
        return self._process_request('RejectAssignment', params)

    def approve_rejected_assignment(self, assignment_id, feedback=None):
        """
        """
        params = {'AssignmentId': assignment_id}
        if feedback:
            params['RequesterFeedback'] = feedback
        return self._process_request('ApproveRejectedAssignment', params)

    def get_file_upload_url(self, assignment_id, question_identifier):
        """
        Generates and returns a temporary URL to an uploaded file. The
        temporary URL is used to retrieve the file as an answer to a
        FileUploadAnswer question, it is valid for 60 seconds.

        Will have a FileUploadURL attribute as per the API Reference.
        """

        params = {'AssignmentId': assignment_id,
                  'QuestionIdentifier': question_identifier}

        return self._process_request('GetFileUploadURL', params,
                                     [('FileUploadURL', FileUploadURL)])

    def get_hit(self, hit_id, response_groups=None):
        """
        """
        params = {'HITId': hit_id}
        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        return self._process_request('GetHIT', params, [('HIT', HIT)])

    def set_reviewing(self, hit_id, revert=None):
        """
        Update a HIT with a status of Reviewable to have a status of Reviewing,
        or reverts a Reviewing HIT back to the Reviewable status.

        Only HITs with a status of Reviewable can be updated with a status of
        Reviewing.  Similarly, only Reviewing HITs can be reverted back to a
        status of Reviewable.
        """
        params = {'HITId': hit_id}
        if revert:
            params['Revert'] = revert
        return self._process_request('SetHITAsReviewing', params)

    def disable_hit(self, hit_id, response_groups=None):
        """
        Remove a HIT from the Mechanical Turk marketplace, approves all
        submitted assignments that have not already been approved or rejected,
        and disposes of the HIT and all assignment data.

        Assignments for the HIT that have already been submitted, but not yet
        approved or rejected, will be automatically approved. Assignments in
        progress at the time of the call to DisableHIT will be approved once
        the assignments are submitted. You will be charged for approval of
        these assignments.  DisableHIT completely disposes of the HIT and
        all submitted assignment data. Assignment results data cannot be
        retrieved for a HIT that has been disposed.

        It is not possible to re-enable a HIT once it has been disabled.
        To make the work from a disabled HIT available again, create a new HIT.
        """
        params = {'HITId': hit_id}
        # Handle optional response groups argument
        if response_groups:
            self.build_list_params(params, response_groups, 'ResponseGroup')

        return self._process_request('DisableHIT', params)

    def dispose_hit(self, hit_id):
        """
        Dispose of a HIT that is no longer needed.

        Only HITs in the "reviewable" state, with all submitted
        assignments approved or rejected, can be disposed. A Requester
        can call GetReviewableHITs to determine which HITs are
        reviewable, then call GetAssignmentsForHIT to retrieve the
        assignments.  Disposing of a HIT removes the HIT from the
        results of a call to GetReviewableHITs.  """
        params = {'HITId': hit_id}
        return self._process_request('DisposeHIT', params)

    def expire_hit(self, hit_id):

        """
        Expire a HIT that is no longer needed.

        The effect is identical to the HIT expiring on its own. The
        HIT no longer appears on the Mechanical Turk web site, and no
        new Workers are allowed to accept the HIT. Workers who have
        accepted the HIT prior to expiration are allowed to complete
        it or return it, or allow the assignment duration to elapse
        (abandon the HIT). Once all remaining assignments have been
        submitted, the expired HIT becomes"reviewable", and will be
        returned by a call to GetReviewableHITs.
        """
        params = {'HITId': hit_id}
        return self._process_request('ForceExpireHIT', params)

    def extend_hit(self, hit_id, assignments_increment=None,
                   expiration_increment=None):
        """
        Increase the maximum number of assignments, or extend the
        expiration date, of an existing HIT.

        NOTE: If a HIT has a status of Reviewable and the HIT is
        extended to make it Available, the HIT will not be returned by
        GetReviewableHITs, and its submitted assignments will not be
        returned by GetAssignmentsForHIT, until the HIT is Reviewable
        again.  Assignment auto-approval will still happen on its
        original schedule, even if the HIT has been extended. Be sure
        to retrieve and approve (or reject) submitted assignments
        before extending the HIT, if so desired.
        """
        # must provide assignment *or* expiration increment
        if (assignments_increment is None and expiration_increment is None) or \
           (assignments_increment is not None and expiration_increment is not None):
            raise ValueError("Must specify either assignments_increment or expiration_increment, but not both")

        params = {'HITId': hit_id}
        if assignments_increment:
            params['MaxAssignmentsIncrement'] = assignments_increment
        if expiration_increment:
            params['ExpirationIncrementInSeconds'] = expiration_increment

        return self._process_request('ExtendHIT', params)

    def get_help(self, about, help_type='Operation'):
        """
        Return information about the Mechanical Turk Service
        operations and response group NOTE - this is basically useless
        as it just returns the URL of the documentation

        help_type: either 'Operation' or 'ResponseGroup'
        """
        params = {'About': about, 'HelpType': help_type}
        return self._process_request('Help', params)

    def grant_bonus(self, worker_id, assignment_id, bonus_price, reason):
        """
        Issues a payment of money from your account to a Worker.  To
        be eligible for a bonus, the Worker must have submitted
        results for one of your HITs, and have had those results
        approved or rejected. This payment happens separately from the
        reward you pay to the Worker when you approve the Worker's
        assignment.  The Bonus must be passed in as an instance of the
        Price object.
        """
        params = bonus_price.get_as_params('BonusAmount', 1)
        params['WorkerId'] = worker_id
        params['AssignmentId'] = assignment_id
        params['Reason'] = reason

        return self._process_request('GrantBonus', params)

    def block_worker(self, worker_id, reason):
        """
        Block a worker from working on my tasks.
        """
        params = {'WorkerId': worker_id, 'Reason': reason}

        return self._process_request('BlockWorker', params)

    def unblock_worker(self, worker_id, reason):
        """
        Unblock a worker from working on my tasks.
        """
        params = {'WorkerId': worker_id, 'Reason': reason}

        return self._process_request('UnblockWorker', params)

    def notify_workers(self, worker_ids, subject, message_text):
        """
        Send a text message to workers.
        """
        params = {'Subject': subject,
                  'MessageText': message_text}
        self.build_list_params(params, worker_ids, 'WorkerId')

        return self._process_request('NotifyWorkers', params)

    def create_qualification_type(self,
                                  name,
                                  description,
                                  status,
                                  keywords=None,
                                  retry_delay=None,
                                  test=None,
                                  answer_key=None,
                                  answer_key_xml=None,
                                  test_duration=None,
                                  auto_granted=False,
                                  auto_granted_value=1):
        """
        Create a new Qualification Type.

        name: This will be visible to workers and must be unique for a
           given requester.

        description: description shown to workers.  Max 2000 characters.

        status: 'Active' or 'Inactive'

        keywords: list of keyword strings or comma separated string.
           Max length of 1000 characters when concatenated with commas.

        retry_delay: number of seconds after requesting a
           qualification the worker must wait before they can ask again.
           If not specified, workers can only request this qualification
           once.

        test: a QuestionForm

        answer_key: an XML string of your answer key, for automatically
           scored qualification tests.
           (Consider implementing an AnswerKey class for this to support.)

        test_duration: the number of seconds a worker has to complete the test.

        auto_granted: if True, requests for the Qualification are granted
           immediately.  Can't coexist with a test.

        auto_granted_value: auto_granted qualifications are given this value.

        """

        params = {'Name': name,
                  'Description': description,
                  'QualificationTypeStatus': status,
                  }
        if retry_delay is not None:
            params['RetryDelayInSeconds'] = retry_delay

        if test is not None:
            assert(isinstance(test, QuestionForm))
            assert(test_duration is not None)
            params['Test'] = test.get_as_xml()

        if test_duration is not None:
            params['TestDurationInSeconds'] = test_duration

        if answer_key is not None:
            if isinstance(answer_key, basestring):
                params['AnswerKey'] = answer_key  # xml
            else:
                raise TypeError
                # Eventually someone will write an AnswerKey class.

        if auto_granted:
            assert(test is None)
            params['AutoGranted'] = True
            params['AutoGrantedValue'] = auto_granted_value

        if keywords:
            params['Keywords'] = self.get_keywords_as_string(keywords)

        return self._process_request('CreateQualificationType', params,
                                     [('QualificationType',
                                       QualificationType)])

    def get_qualification_type(self, qualification_type_id):
        params = {'QualificationTypeId': qualification_type_id }
        return self._process_request('GetQualificationType', params,
                                     [('QualificationType', QualificationType)])

    def get_all_qualifications_for_qual_type(self, qualification_type_id):
        page_size = 100
        search_qual = self.get_qualifications_for_qualification_type(qualification_type_id)
        total_records = int(search_qual.TotalNumResults)
        get_page_quals = lambda page: self.get_qualifications_for_qualification_type(qualification_type_id = qualification_type_id, page_size=page_size, page_number = page)
        page_nums = self._get_pages(page_size, total_records)
        qual_sets = itertools.imap(get_page_quals, page_nums)
        return itertools.chain.from_iterable(qual_sets)

    def get_qualifications_for_qualification_type(self, qualification_type_id, page_size=100, page_number = 1):
        params = {'QualificationTypeId': qualification_type_id,
                  'PageSize': page_size,
                  'PageNumber': page_number}
        return self._process_request('GetQualificationsForQualificationType', params,
                                     [('Qualification', Qualification)])

    def update_qualification_type(self, qualification_type_id,
                                  description=None,
                                  status=None,
                                  retry_delay=None,
                                  test=None,
                                  answer_key=None,
                                  test_duration=None,
                                  auto_granted=None,
                                  auto_granted_value=None):

        params = {'QualificationTypeId': qualification_type_id}

        if description is not None:
            params['Description'] = description

        if status is not None:
            params['QualificationTypeStatus'] = status

        if retry_delay is not None:
            params['RetryDelayInSeconds'] = retry_delay

        if test is not None:
            assert(isinstance(test, QuestionForm))
            params['Test'] = test.get_as_xml()

        if test_duration is not None:
            params['TestDurationInSeconds'] = test_duration

        if answer_key is not None:
            if isinstance(answer_key, basestring):
                params['AnswerKey'] = answer_key  # xml
            else:
                raise TypeError
                # Eventually someone will write an AnswerKey class.

        if auto_granted is not None:
            params['AutoGranted'] = auto_granted

        if auto_granted_value is not None:
            params['AutoGrantedValue'] = auto_granted_value

        return self._process_request('UpdateQualificationType', params,
                                     [('QualificationType', QualificationType)])

    def dispose_qualification_type(self, qualification_type_id):
        """TODO: Document."""
        params = {'QualificationTypeId': qualification_type_id}
        return self._process_request('DisposeQualificationType', params)

    def search_qualification_types(self, query=None, sort_by='Name',
                                   sort_direction='Ascending', page_size=10,
                                   page_number=1, must_be_requestable=True,
                                   must_be_owned_by_caller=True):
        """TODO: Document."""
        params = {'Query': query,
                  'SortProperty': sort_by,
                  'SortDirection': sort_direction,
                  'PageSize': page_size,
                  'PageNumber': page_number,
                  'MustBeRequestable': must_be_requestable,
                  'MustBeOwnedByCaller': must_be_owned_by_caller}
        return self._process_request('SearchQualificationTypes', params,
                    [('QualificationType', QualificationType)])

    def get_qualification_requests(self, qualification_type_id,
                                   sort_by='Expiration',
                                   sort_direction='Ascending', page_size=10,
                                   page_number=1):
        """TODO: Document."""
        params = {'QualificationTypeId': qualification_type_id,
                  'SortProperty': sort_by,
                  'SortDirection': sort_direction,
                  'PageSize': page_size,
                  'PageNumber': page_number}
        return self._process_request('GetQualificationRequests', params,
                    [('QualificationRequest', QualificationRequest)])

    def grant_qualification(self, qualification_request_id, integer_value=1):
        """TODO: Document."""
        params = {'QualificationRequestId': qualification_request_id,
                  'IntegerValue': integer_value}
        return self._process_request('GrantQualification', params)

    def revoke_qualification(self, subject_id, qualification_type_id,
                             reason=None):
        """TODO: Document."""
        params = {'SubjectId': subject_id,
                  'QualificationTypeId': qualification_type_id,
                  'Reason': reason}
        return self._process_request('RevokeQualification', params)

    def assign_qualification(self, qualification_type_id, worker_id,
                             value=1, send_notification=True):
        params = {'QualificationTypeId': qualification_type_id,
                  'WorkerId' : worker_id,
                  'IntegerValue' : value,
                  'SendNotification' : send_notification}
        return self._process_request('AssignQualification', params)

    def get_qualification_score(self, qualification_type_id, worker_id):
        """TODO: Document."""
        params = {'QualificationTypeId' : qualification_type_id,
                  'SubjectId' : worker_id}
        return self._process_request('GetQualificationScore', params,
                    [('Qualification', Qualification)])

    def update_qualification_score(self, qualification_type_id, worker_id,
                                   value):
        """TODO: Document."""
        params = {'QualificationTypeId' : qualification_type_id,
                  'SubjectId' : worker_id,
                  'IntegerValue' : value}
        return self._process_request('UpdateQualificationScore', params)

    def _process_request(self, request_type, params, marker_elems=None):
        """
        Helper to process the xml response from AWS
        """
        params['Operation'] = request_type
        response = self.make_request(None, params, verb='POST')
        return self._process_response(response, marker_elems)

    def _process_response(self, response, marker_elems=None):
        """
        Helper to process the xml response from AWS
        """
        body = response.read()
        if self.debug == 2:
            print(body)
        if '<Errors>' not in body.decode('utf-8'):
            rs = ResultSet(marker_elems)
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs
        else:
            raise MTurkRequestError(response.status, response.reason, body)

    @staticmethod
    def get_keywords_as_string(keywords):
        """
        Returns a comma+space-separated string of keywords from either
        a list or a string
        """
        if isinstance(keywords, list):
            keywords = ', '.join(keywords)
        if isinstance(keywords, str):
            final_keywords = keywords
        elif isinstance(keywords, unicode):
            final_keywords = keywords.encode('utf-8')
        elif keywords is None:
            final_keywords = ""
        else:
            raise TypeError("keywords argument must be a string or a list of strings; got a %s" % type(keywords))
        return final_keywords

    @staticmethod
    def get_price_as_price(reward):
        """
        Returns a Price data structure from either a float or a Price
        """
        if isinstance(reward, Price):
            final_price = reward
        else:
            final_price = Price(reward)
        return final_price

    @staticmethod
    def duration_as_seconds(duration):
        if isinstance(duration, datetime.timedelta):
            duration = duration.days * 86400 + duration.seconds
        try:
            duration = int(duration)
        except TypeError:
            raise TypeError("Duration must be a timedelta or int-castable, got %s" % type(duration))
        return duration


class BaseAutoResultElement(object):
    """
    Base class to automatically add attributes when parsing XML
    """
    def __init__(self, connection):
        pass

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)


class HIT(BaseAutoResultElement):
    """
    Class to extract a HIT structure from a response (used in ResultSet)

    Will have attributes named as per the Developer Guide,
    e.g. HITId, HITTypeId, CreationTime
    """

    # property helper to determine if HIT has expired
    def _has_expired(self):
        """ Has this HIT expired yet? """
        expired = False
        if hasattr(self, 'Expiration'):
            now = datetime.datetime.utcnow()
            expiration = datetime.datetime.strptime(self.Expiration, '%Y-%m-%dT%H:%M:%SZ')
            expired = (now >= expiration)
        else:
            raise ValueError("ERROR: Request for expired property, but no Expiration in HIT!")
        return expired

    # are we there yet?
    expired = property(_has_expired)


class FileUploadURL(BaseAutoResultElement):
    """
    Class to extract an FileUploadURL structure from a response
    """

    pass


class HITTypeId(BaseAutoResultElement):
    """
    Class to extract an HITTypeId structure from a response
    """

    pass


class Qualification(BaseAutoResultElement):
    """
    Class to extract an Qualification structure from a response (used in
    ResultSet)

    Will have attributes named as per the Developer Guide such as
    QualificationTypeId, IntegerValue. Does not seem to contain GrantTime.
    """

    pass


class QualificationType(BaseAutoResultElement):
    """
    Class to extract an QualificationType structure from a response (used in
    ResultSet)

    Will have attributes named as per the Developer Guide,
    e.g. QualificationTypeId, CreationTime, Name, etc
    """

    pass


class QualificationRequest(BaseAutoResultElement):
    """
    Class to extract an QualificationRequest structure from a response (used in
    ResultSet)

    Will have attributes named as per the Developer Guide,
    e.g. QualificationRequestId, QualificationTypeId, SubjectId, etc
    """

    def __init__(self, connection):
        super(QualificationRequest, self).__init__(connection)
        self.answers = []

    def endElement(self, name, value, connection):
        # the answer consists of embedded XML, so it needs to be parsed independantly
        if name == 'Answer':
            answer_rs = ResultSet([('Answer', QuestionFormAnswer)])
            h = handler.XmlHandler(answer_rs, connection)
            value = connection.get_utf8able_str(value)
            xml.sax.parseString(value, h)
            self.answers.append(answer_rs)
        else:
            super(QualificationRequest, self).endElement(name, value, connection)


class Assignment(BaseAutoResultElement):
    """
    Class to extract an Assignment structure from a response (used in
    ResultSet)

    Will have attributes named as per the Developer Guide,
    e.g. AssignmentId, WorkerId, HITId, Answer, etc
    """

    def __init__(self, connection):
        super(Assignment, self).__init__(connection)
        self.answers = []

    def endElement(self, name, value, connection):
        # the answer consists of embedded XML, so it needs to be parsed independantly
        if name == 'Answer':
            answer_rs = ResultSet([('Answer', QuestionFormAnswer)])
            h = handler.XmlHandler(answer_rs, connection)
            value = connection.get_utf8able_str(value)
            xml.sax.parseString(value, h)
            self.answers.append(answer_rs)
        else:
            super(Assignment, self).endElement(name, value, connection)


class QuestionFormAnswer(BaseAutoResultElement):
    """
    Class to extract Answers from inside the embedded XML
    QuestionFormAnswers element inside the Answer element which is
    part of the Assignment and QualificationRequest structures

    A QuestionFormAnswers element contains an Answer element for each
    question in the HIT or Qualification test for which the Worker
    provided an answer. Each Answer contains a QuestionIdentifier
    element whose value corresponds to the QuestionIdentifier of a
    Question in the QuestionForm. See the QuestionForm data structure
    for more information about questions and answer specifications.

    If the question expects a free-text answer, the Answer element
    contains a FreeText element. This element contains the Worker's
    answer

    *NOTE* - currently really only supports free-text and selection answers
    """

    def __init__(self, connection):
        super(QuestionFormAnswer, self).__init__(connection)
        self.fields = []
        self.qid = None

    def endElement(self, name, value, connection):
        if name == 'QuestionIdentifier':
            self.qid = value
        elif name in ['FreeText', 'SelectionIdentifier', 'OtherSelectionText'] and self.qid:
            self.fields.append(value)
