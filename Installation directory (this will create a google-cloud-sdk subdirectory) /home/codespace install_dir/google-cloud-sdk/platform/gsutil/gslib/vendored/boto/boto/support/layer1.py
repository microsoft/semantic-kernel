# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.support import exceptions


class SupportConnection(AWSQueryConnection):
    """
    AWS Support
    The AWS Support API reference is intended for programmers who need
    detailed information about the AWS Support operations and data
    types. This service enables you to manage your AWS Support cases
    programmatically. It uses HTTP methods that return results in JSON
    format.

    The AWS Support service also exposes a set of `Trusted Advisor`_
    features. You can retrieve a list of checks and their
    descriptions, get check results, specify checks to refresh, and
    get the refresh status of checks.

    The following list describes the AWS Support case management
    operations:


    + **Service names, issue categories, and available severity
      levels. **The DescribeServices and DescribeSeverityLevels
      operations return AWS service names, service codes, service
      categories, and problem severity levels. You use these values when
      you call the CreateCase operation.
    + **Case creation, case details, and case resolution.** The
      CreateCase, DescribeCases, DescribeAttachment, and ResolveCase
      operations create AWS Support cases, retrieve information about
      cases, and resolve cases.
    + **Case communication.** The DescribeCommunications,
      AddCommunicationToCase, and AddAttachmentsToSet operations
      retrieve and add communications and attachments to AWS Support
      cases.


    The following list describes the operations available from the AWS
    Support service for Trusted Advisor:


    + DescribeTrustedAdvisorChecks returns the list of checks that run
      against your AWS resources.
    + Using the `CheckId` for a specific check returned by
      DescribeTrustedAdvisorChecks, you can call
      DescribeTrustedAdvisorCheckResult to obtain the results for the
      check you specified.
    + DescribeTrustedAdvisorCheckSummaries returns summarized results
      for one or more Trusted Advisor checks.
    + RefreshTrustedAdvisorCheck requests that Trusted Advisor rerun a
      specified check.
    + DescribeTrustedAdvisorCheckRefreshStatuses reports the refresh
      status of one or more checks.


    For authentication of requests, AWS Support uses `Signature
    Version 4 Signing Process`_.

    See `About the AWS Support API`_ in the AWS Support User Guide for
    information about how to use this service to create and manage
    your support cases, and how to call Trusted Advisor for results of
    checks on your resources.
    """
    APIVersion = "2013-04-15"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "support.us-east-1.amazonaws.com"
    ServiceName = "Support"
    TargetPrefix = "AWSSupport_20130415"
    ResponseError = JSONResponseError

    _faults = {
        "CaseCreationLimitExceeded": exceptions.CaseCreationLimitExceeded,
        "AttachmentLimitExceeded": exceptions.AttachmentLimitExceeded,
        "CaseIdNotFound": exceptions.CaseIdNotFound,
        "DescribeAttachmentLimitExceeded": exceptions.DescribeAttachmentLimitExceeded,
        "AttachmentSetIdNotFound": exceptions.AttachmentSetIdNotFound,
        "InternalServerError": exceptions.InternalServerError,
        "AttachmentSetExpired": exceptions.AttachmentSetExpired,
        "AttachmentIdNotFound": exceptions.AttachmentIdNotFound,
        "AttachmentSetSizeLimitExceeded": exceptions.AttachmentSetSizeLimitExceeded,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(SupportConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_attachments_to_set(self, attachments, attachment_set_id=None):
        """
        Adds one or more attachments to an attachment set. If an
        `AttachmentSetId` is not specified, a new attachment set is
        created, and the ID of the set is returned in the response. If
        an `AttachmentSetId` is specified, the attachments are added
        to the specified set, if it exists.

        An attachment set is a temporary container for attachments
        that are to be added to a case or case communication. The set
        is available for one hour after it is created; the
        `ExpiryTime` returned in the response indicates when the set
        expires. The maximum number of attachments in a set is 3, and
        the maximum size of any attachment in the set is 5 MB.

        :type attachment_set_id: string
        :param attachment_set_id: The ID of the attachment set. If an
            `AttachmentSetId` is not specified, a new attachment set is
            created, and the ID of the set is returned in the response. If an
            `AttachmentSetId` is specified, the attachments are added to the
            specified set, if it exists.

        :type attachments: list
        :param attachments: One or more attachments to add to the set. The
            limit is 3 attachments per set, and the size limit is 5 MB per
            attachment.

        """
        params = {'attachments': attachments, }
        if attachment_set_id is not None:
            params['attachmentSetId'] = attachment_set_id
        return self.make_request(action='AddAttachmentsToSet',
                                 body=json.dumps(params))

    def add_communication_to_case(self, communication_body, case_id=None,
                                  cc_email_addresses=None,
                                  attachment_set_id=None):
        """
        Adds additional customer communication to an AWS Support case.
        You use the `CaseId` value to identify the case to add
        communication to. You can list a set of email addresses to
        copy on the communication using the `CcEmailAddresses` value.
        The `CommunicationBody` value contains the text of the
        communication.

        The response indicates the success or failure of the request.

        This operation implements a subset of the behavior on the AWS
        Support `Your Support Cases`_ web form.

        :type case_id: string
        :param case_id: The AWS Support case ID requested or returned in the
            call. The case ID is an alphanumeric string formatted as shown in
            this example: case- 12345678910-2013-c4c1d2bf33c5cf47

        :type communication_body: string
        :param communication_body: The body of an email communication to add to
            the support case.

        :type cc_email_addresses: list
        :param cc_email_addresses: The email addresses in the CC line of an
            email to be added to the support case.

        :type attachment_set_id: string
        :param attachment_set_id: The ID of a set of one or more attachments
            for the communication to add to the case. Create the set by calling
            AddAttachmentsToSet

        """
        params = {'communicationBody': communication_body, }
        if case_id is not None:
            params['caseId'] = case_id
        if cc_email_addresses is not None:
            params['ccEmailAddresses'] = cc_email_addresses
        if attachment_set_id is not None:
            params['attachmentSetId'] = attachment_set_id
        return self.make_request(action='AddCommunicationToCase',
                                 body=json.dumps(params))

    def create_case(self, subject, communication_body, service_code=None,
                    severity_code=None, category_code=None,
                    cc_email_addresses=None, language=None, issue_type=None,
                    attachment_set_id=None):
        """
        Creates a new case in the AWS Support Center. This operation
        is modeled on the behavior of the AWS Support Center `Open a
        new case`_ page. Its parameters require you to specify the
        following information:


        #. **IssueType.** The type of issue for the case. You can
           specify either "customer-service" or "technical." If you do
           not indicate a value, the default is "technical."
        #. **ServiceCode.** The code for an AWS service. You obtain
           the `ServiceCode` by calling DescribeServices.
        #. **CategoryCode.** The category for the service defined for
           the `ServiceCode` value. You also obtain the category code for
           a service by calling DescribeServices. Each AWS service
           defines its own set of category codes.
        #. **SeverityCode.** A value that indicates the urgency of the
           case, which in turn determines the response time according to
           your service level agreement with AWS Support. You obtain the
           SeverityCode by calling DescribeSeverityLevels.
        #. **Subject.** The **Subject** field on the AWS Support
           Center `Open a new case`_ page.
        #. **CommunicationBody.** The **Description** field on the AWS
           Support Center `Open a new case`_ page.
        #. **AttachmentSetId.** The ID of a set of attachments that
           has been created by using AddAttachmentsToSet.
        #. **Language.** The human language in which AWS Support
           handles the case. English and Japanese are currently
           supported.
        #. **CcEmailAddresses.** The AWS Support Center **CC** field
           on the `Open a new case`_ page. You can list email addresses
           to be copied on any correspondence about the case. The account
           that opens the case is already identified by passing the AWS
           Credentials in the HTTP POST method or in a method or function
           call from one of the programming languages supported by an
           `AWS SDK`_.


        A successful CreateCase request returns an AWS Support case
        number. Case numbers are used by the DescribeCases operation
        to retrieve existing AWS Support cases.

        :type subject: string
        :param subject: The title of the AWS Support case.

        :type service_code: string
        :param service_code: The code for the AWS service returned by the call
            to DescribeServices.

        :type severity_code: string
        :param severity_code: The code for the severity level returned by the
            call to DescribeSeverityLevels.

        :type category_code: string
        :param category_code: The category of problem for the AWS Support case.

        :type communication_body: string
        :param communication_body: The communication body text when you create
            an AWS Support case by calling CreateCase.

        :type cc_email_addresses: list
        :param cc_email_addresses: A list of email addresses that AWS Support
            copies on case correspondence.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        :type issue_type: string
        :param issue_type: The type of issue for the case. You can specify
            either "customer-service" or "technical." If you do not indicate a
            value, the default is "technical."

        :type attachment_set_id: string
        :param attachment_set_id: The ID of a set of one or more attachments
            for the case. Create the set by using AddAttachmentsToSet.

        """
        params = {
            'subject': subject,
            'communicationBody': communication_body,
        }
        if service_code is not None:
            params['serviceCode'] = service_code
        if severity_code is not None:
            params['severityCode'] = severity_code
        if category_code is not None:
            params['categoryCode'] = category_code
        if cc_email_addresses is not None:
            params['ccEmailAddresses'] = cc_email_addresses
        if language is not None:
            params['language'] = language
        if issue_type is not None:
            params['issueType'] = issue_type
        if attachment_set_id is not None:
            params['attachmentSetId'] = attachment_set_id
        return self.make_request(action='CreateCase',
                                 body=json.dumps(params))

    def describe_attachment(self, attachment_id):
        """
        Returns the attachment that has the specified ID. Attachment
        IDs are generated by the case management system when you add
        an attachment to a case or case communication. Attachment IDs
        are returned in the AttachmentDetails objects that are
        returned by the DescribeCommunications operation.

        :type attachment_id: string
        :param attachment_id: The ID of the attachment to return. Attachment
            IDs are returned by the DescribeCommunications operation.

        """
        params = {'attachmentId': attachment_id, }
        return self.make_request(action='DescribeAttachment',
                                 body=json.dumps(params))

    def describe_cases(self, case_id_list=None, display_id=None,
                       after_time=None, before_time=None,
                       include_resolved_cases=None, next_token=None,
                       max_results=None, language=None,
                       include_communications=None):
        """
        Returns a list of cases that you specify by passing one or
        more case IDs. In addition, you can filter the cases by date
        by setting values for the `AfterTime` and `BeforeTime` request
        parameters.

        Case data is available for 12 months after creation. If a case
        was created more than 12 months ago, a request for data might
        cause an error.

        The response returns the following in JSON format:


        #. One or more CaseDetails data types.
        #. One or more `NextToken` values, which specify where to
           paginate the returned records represented by the `CaseDetails`
           objects.

        :type case_id_list: list
        :param case_id_list: A list of ID numbers of the support cases you want
            returned. The maximum number of cases is 100.

        :type display_id: string
        :param display_id: The ID displayed for a case in the AWS Support
            Center user interface.

        :type after_time: string
        :param after_time: The start date for a filtered date search on support
            case communications. Case communications are available for 12
            months after creation.

        :type before_time: string
        :param before_time: The end date for a filtered date search on support
            case communications. Case communications are available for 12
            months after creation.

        :type include_resolved_cases: boolean
        :param include_resolved_cases: Specifies whether resolved support cases
            should be included in the DescribeCases results. The default is
            false .

        :type next_token: string
        :param next_token: A resumption point for pagination.

        :type max_results: integer
        :param max_results: The maximum number of results to return before
            paginating.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        :type include_communications: boolean
        :param include_communications: Specifies whether communications should
            be included in the DescribeCases results. The default is true .

        """
        params = {}
        if case_id_list is not None:
            params['caseIdList'] = case_id_list
        if display_id is not None:
            params['displayId'] = display_id
        if after_time is not None:
            params['afterTime'] = after_time
        if before_time is not None:
            params['beforeTime'] = before_time
        if include_resolved_cases is not None:
            params['includeResolvedCases'] = include_resolved_cases
        if next_token is not None:
            params['nextToken'] = next_token
        if max_results is not None:
            params['maxResults'] = max_results
        if language is not None:
            params['language'] = language
        if include_communications is not None:
            params['includeCommunications'] = include_communications
        return self.make_request(action='DescribeCases',
                                 body=json.dumps(params))

    def describe_communications(self, case_id, before_time=None,
                                after_time=None, next_token=None,
                                max_results=None):
        """
        Returns communications (and attachments) for one or more
        support cases. You can use the `AfterTime` and `BeforeTime`
        parameters to filter by date. You can use the `CaseId`
        parameter to restrict the results to a particular case.

        Case data is available for 12 months after creation. If a case
        was created more than 12 months ago, a request for data might
        cause an error.

        You can use the `MaxResults` and `NextToken` parameters to
        control the pagination of the result set. Set `MaxResults` to
        the number of cases you want displayed on each page, and use
        `NextToken` to specify the resumption of pagination.

        :type case_id: string
        :param case_id: The AWS Support case ID requested or returned in the
            call. The case ID is an alphanumeric string formatted as shown in
            this example: case- 12345678910-2013-c4c1d2bf33c5cf47

        :type before_time: string
        :param before_time: The end date for a filtered date search on support
            case communications. Case communications are available for 12
            months after creation.

        :type after_time: string
        :param after_time: The start date for a filtered date search on support
            case communications. Case communications are available for 12
            months after creation.

        :type next_token: string
        :param next_token: A resumption point for pagination.

        :type max_results: integer
        :param max_results: The maximum number of results to return before
            paginating.

        """
        params = {'caseId': case_id, }
        if before_time is not None:
            params['beforeTime'] = before_time
        if after_time is not None:
            params['afterTime'] = after_time
        if next_token is not None:
            params['nextToken'] = next_token
        if max_results is not None:
            params['maxResults'] = max_results
        return self.make_request(action='DescribeCommunications',
                                 body=json.dumps(params))

    def describe_services(self, service_code_list=None, language=None):
        """
        Returns the current list of AWS services and a list of service
        categories that applies to each one. You then use service
        names and categories in your CreateCase requests. Each AWS
        service has its own set of categories.

        The service codes and category codes correspond to the values
        that are displayed in the **Service** and **Category** drop-
        down lists on the AWS Support Center `Open a new case`_ page.
        The values in those fields, however, do not necessarily match
        the service codes and categories returned by the
        `DescribeServices` request. Always use the service codes and
        categories obtained programmatically. This practice ensures
        that you always have the most recent set of service and
        category codes.

        :type service_code_list: list
        :param service_code_list: A JSON-formatted list of service codes
            available for AWS services.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        """
        params = {}
        if service_code_list is not None:
            params['serviceCodeList'] = service_code_list
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeServices',
                                 body=json.dumps(params))

    def describe_severity_levels(self, language=None):
        """
        Returns the list of severity levels that you can assign to an
        AWS Support case. The severity level for a case is also a
        field in the CaseDetails data type included in any CreateCase
        request.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        """
        params = {}
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeSeverityLevels',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_refresh_statuses(self, check_ids):
        """
        Returns the refresh status of the Trusted Advisor checks that
        have the specified check IDs. Check IDs can be obtained by
        calling DescribeTrustedAdvisorChecks.

        :type check_ids: list
        :param check_ids: The IDs of the Trusted Advisor checks.

        """
        params = {'checkIds': check_ids, }
        return self.make_request(action='DescribeTrustedAdvisorCheckRefreshStatuses',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_result(self, check_id, language=None):
        """
        Returns the results of the Trusted Advisor check that has the
        specified check ID. Check IDs can be obtained by calling
        DescribeTrustedAdvisorChecks.

        The response contains a TrustedAdvisorCheckResult object,
        which contains these three objects:


        + TrustedAdvisorCategorySpecificSummary
        + TrustedAdvisorResourceDetail
        + TrustedAdvisorResourcesSummary


        In addition, the response contains these fields:


        + **Status.** The alert status of the check: "ok" (green),
          "warning" (yellow), "error" (red), or "not_available".
        + **Timestamp.** The time of the last refresh of the check.
        + **CheckId.** The unique identifier for the check.

        :type check_id: string
        :param check_id: The unique identifier for the Trusted Advisor check.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        """
        params = {'checkId': check_id, }
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeTrustedAdvisorCheckResult',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_summaries(self, check_ids):
        """
        Returns the summaries of the results of the Trusted Advisor
        checks that have the specified check IDs. Check IDs can be
        obtained by calling DescribeTrustedAdvisorChecks.

        The response contains an array of TrustedAdvisorCheckSummary
        objects.

        :type check_ids: list
        :param check_ids: The IDs of the Trusted Advisor checks.

        """
        params = {'checkIds': check_ids, }
        return self.make_request(action='DescribeTrustedAdvisorCheckSummaries',
                                 body=json.dumps(params))

    def describe_trusted_advisor_checks(self, language):
        """
        Returns information about all available Trusted Advisor
        checks, including name, ID, category, description, and
        metadata. You must specify a language code; English ("en") and
        Japanese ("ja") are currently supported. The response contains
        a TrustedAdvisorCheckDescription for each check.

        :type language: string
        :param language: The ISO 639-1 code for the language in which AWS
            provides support. AWS Support currently supports English ("en") and
            Japanese ("ja"). Language parameters must be passed explicitly for
            operations that take them.

        """
        params = {'language': language, }
        return self.make_request(action='DescribeTrustedAdvisorChecks',
                                 body=json.dumps(params))

    def refresh_trusted_advisor_check(self, check_id):
        """
        Requests a refresh of the Trusted Advisor check that has the
        specified check ID. Check IDs can be obtained by calling
        DescribeTrustedAdvisorChecks.

        The response contains a RefreshTrustedAdvisorCheckResult
        object, which contains these fields:


        + **Status.** The refresh status of the check: "none",
          "enqueued", "processing", "success", or "abandoned".
        + **MillisUntilNextRefreshable.** The amount of time, in
          milliseconds, until the check is eligible for refresh.
        + **CheckId.** The unique identifier for the check.

        :type check_id: string
        :param check_id: The unique identifier for the Trusted Advisor check.

        """
        params = {'checkId': check_id, }
        return self.make_request(action='RefreshTrustedAdvisorCheck',
                                 body=json.dumps(params))

    def resolve_case(self, case_id=None):
        """
        Takes a `CaseId` and returns the initial state of the case
        along with the state of the case after the call to ResolveCase
        completed.

        :type case_id: string
        :param case_id: The AWS Support case ID requested or returned in the
            call. The case ID is an alphanumeric string formatted as shown in
            this example: case- 12345678910-2013-c4c1d2bf33c5cf47

        """
        params = {}
        if case_id is not None:
            params['caseId'] = case_id
        return self.make_request(action='ResolveCase',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
