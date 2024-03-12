# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

import boto
from boto.cloudformation.stack import Stack, StackSummary, StackEvent
from boto.cloudformation.stack import StackResource, StackResourceSummary
from boto.cloudformation.template import Template
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.compat import json


class CloudFormationConnection(AWSQueryConnection):
    """
    AWS CloudFormation
    AWS CloudFormation enables you to create and manage AWS
    infrastructure deployments predictably and repeatedly. AWS
    CloudFormation helps you leverage AWS products such as Amazon EC2,
    EBS, Amazon SNS, ELB, and Auto Scaling to build highly-reliable,
    highly scalable, cost effective applications without worrying
    about creating and configuring the underlying AWS infrastructure.

    With AWS CloudFormation, you declare all of your resources and
    dependencies in a template file. The template defines a collection
    of resources as a single unit called a stack. AWS CloudFormation
    creates and deletes all member resources of the stack together and
    manages all dependencies between the resources for you.

    For more information about this product, go to the `CloudFormation
    Product Page`_.

    Amazon CloudFormation makes use of other AWS products. If you need
    additional technical information about a specific AWS product, you
    can find the product's technical documentation at
    `http://aws.amazon.com/documentation/`_.
    """
    APIVersion = boto.config.get('Boto', 'cfn_version', '2010-05-15')
    DefaultRegionName = boto.config.get('Boto', 'cfn_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto', 'cfn_region_endpoint',
                                            'cloudformation.us-east-1.amazonaws.com')

    valid_states = (
        'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE',
        'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE',
        'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'DELETE_COMPLETE',
        'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
        'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS',
        'UPDATE_ROLLBACK_FAILED',
        'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
        'UPDATE_ROLLBACK_COMPLETE')

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 converter=None, security_token=None, validate_certs=True,
                 profile_name=None):
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                self.DefaultRegionEndpoint, CloudFormationConnection)
        self.region = region
        super(CloudFormationConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    security_token,
                                    validate_certs=validate_certs,
                                    profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def encode_bool(self, v):
        v = bool(v)
        return {True: "true", False: "false"}[v]

    def _build_create_or_update_params(self, stack_name, template_body,
            template_url, parameters, disable_rollback, timeout_in_minutes,
            notification_arns, capabilities, on_failure, stack_policy_body,
            stack_policy_url, tags, use_previous_template=None,
            stack_policy_during_update_body=None,
            stack_policy_during_update_url=None):
        """
        Helper that creates JSON parameters needed by a Stack Create or
        Stack Update call.

        :type stack_name: string
        :param stack_name:
        The name associated with the stack. The name must be unique within your
            AWS account.

        Must contain only alphanumeric characters (case sensitive) and start
            with an alpha character. Maximum length of the name is 255
            characters.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`. If both `TemplateBody` and
            `TemplateUrl` are passed, only `TemplateBody` is used.
            `TemplateBody`.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to the `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`. If both `TemplateBody` and
            `TemplateUrl` are passed, only `TemplateBody` is used.
            `TemplateBody`.

        :type parameters: list
        :param parameters: A list of key/value tuples that specify input
            parameters for the stack. A 3-tuple (key, value, bool) may be used to
            specify the `UsePreviousValue` option.

        :type disable_rollback: boolean
        :param disable_rollback: Set to `True` to disable rollback of the stack
            if stack creation failed. You can specify either `DisableRollback`
            or `OnFailure`, but not both.
        Default: `False`

        :type timeout_in_minutes: integer
        :param timeout_in_minutes: The amount of time that can pass before the
            stack status becomes CREATE_FAILED; if `DisableRollback` is not set
            or is set to `False`, the stack will be rolled back.

        :type notification_arns: list
        :param notification_arns: The Simple Notification Service (SNS) topic
            ARNs to publish stack related events. You can find your SNS topic
            ARNs using the `SNS console`_ or your Command Line Interface (CLI).

        :type capabilities: list
        :param capabilities: The list of capabilities that you want to allow in
            the stack. If your template contains certain resources, you must
            specify the CAPABILITY_IAM value for this parameter; otherwise,
            this action returns an InsufficientCapabilities error. The
            following resources require you to specify the capabilities
            parameter: `AWS::CloudFormation::Stack`_, `AWS::IAM::AccessKey`_,
            `AWS::IAM::Group`_, `AWS::IAM::InstanceProfile`_,
            `AWS::IAM::Policy`_, `AWS::IAM::Role`_, `AWS::IAM::User`_, and
            `AWS::IAM::UserToGroupAddition`_.

        :type on_failure: string
        :param on_failure: Determines what action will be taken if stack
            creation fails. This must be one of: DO_NOTHING, ROLLBACK, or
            DELETE. You can specify either `OnFailure` or `DisableRollback`,
            but not both.
        Default: `ROLLBACK`

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the stack policy body.
            (For more information, go to ` Prevent Updates to Stack Resources`_
            in the AWS CloudFormation User Guide.)
        If you pass `StackPolicyBody` and `StackPolicyURL`, only
            `StackPolicyBody` is used.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the stack
            policy. The URL must point to a policy (max size: 16KB) located in
            an S3 bucket in the same region as the stack. If you pass
            `StackPolicyBody` and `StackPolicyURL`, only `StackPolicyBody` is
            used.

        :type tags: list
        :param tags: A set of user-defined `Tags` to associate with this stack,
            represented by key/value pairs. Tags defined for the stack are
            propagated to EC2 resources that are created as part of the stack.
            A maximum number of 10 tags can be specified.

        :type use_previous_template: boolean
        :param use_previous_template: Set to `True` to use the previous
            template instead of uploading a new one via `TemplateBody` or
            `TemplateURL`.
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`.

        :type stack_policy_during_update_body: string
        :param stack_policy_during_update_body: Structure containing the
            temporary overriding stack policy body. If you pass
            `StackPolicyDuringUpdateBody` and `StackPolicyDuringUpdateURL`,
            only `StackPolicyDuringUpdateBody` is used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that associated with the stack
            will be used.

        :type stack_policy_during_update_url: string
        :param stack_policy_during_update_url: Location of a file containing
            the temporary overriding stack policy. The URL must point to a
            policy (max size: 16KB) located in an S3 bucket in the same region
            as the stack. If you pass `StackPolicyDuringUpdateBody` and
            `StackPolicyDuringUpdateURL`, only `StackPolicyDuringUpdateBody` is
            used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that is associated with the stack
            will be used.

        :rtype: dict
        :return: JSON parameters represented as a Python dict.
        """
        params = {'ContentType': "JSON", 'StackName': stack_name,
                'DisableRollback': self.encode_bool(disable_rollback)}
        if template_body:
            params['TemplateBody'] = template_body
        if template_url:
            params['TemplateURL'] = template_url
        if use_previous_template is not None:
            params['UsePreviousTemplate'] = self.encode_bool(use_previous_template)
        if template_body and template_url:
            boto.log.warning("If both TemplateBody and TemplateURL are"
                " specified, only TemplateBody will be honored by the API")
        if parameters and len(parameters) > 0:
            for i, parameter_tuple in enumerate(parameters):
                key, value = parameter_tuple[:2]
                use_previous = (parameter_tuple[2]
                                if len(parameter_tuple) > 2 else False)
                params['Parameters.member.%d.ParameterKey' % (i + 1)] = key
                if use_previous:
                    params['Parameters.member.%d.UsePreviousValue'
                           % (i + 1)] = self.encode_bool(use_previous)
                else:
                    params['Parameters.member.%d.ParameterValue' % (i + 1)] = value

        if capabilities:
            for i, value in enumerate(capabilities):
                params['Capabilities.member.%d' % (i + 1)] = value
        if tags:
            for i, (key, value) in enumerate(tags.items()):
                params['Tags.member.%d.Key' % (i + 1)] = key
                params['Tags.member.%d.Value' % (i + 1)] = value
        if notification_arns and len(notification_arns) > 0:
            self.build_list_params(params, notification_arns,
                                   "NotificationARNs.member")
        if timeout_in_minutes:
            params['TimeoutInMinutes'] = int(timeout_in_minutes)
        if disable_rollback is not None:
            params['DisableRollback'] = str(
                disable_rollback).lower()
        if on_failure is not None:
            params['OnFailure'] = on_failure
        if stack_policy_body is not None:
            params['StackPolicyBody'] = stack_policy_body
        if stack_policy_url is not None:
            params['StackPolicyURL'] = stack_policy_url
        if stack_policy_during_update_body is not None:
            params['StackPolicyDuringUpdateBody'] = stack_policy_during_update_body
        if stack_policy_during_update_url is not None:
            params['StackPolicyDuringUpdateURL'] = stack_policy_during_update_url
        return params

    def _do_request(self, call, params, path, method):
        """
        Do a request via ``self.make_request`` and parse the JSON response.

        :type call: string
        :param call: Call name, e.g. ``CreateStack``

        :type params: dict
        :param params: Dictionary of call parameters

        :type path: string
        :param path: Server path

        :type method: string
        :param method: HTTP method to use

        :rtype: dict
        :return: Parsed JSON response data
        """
        response = self.make_request(call, params, path, method)
        body = response.read().decode('utf-8')
        if response.status == 200:
            body = json.loads(body)
            return body
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body=body)

    def create_stack(self, stack_name, template_body=None, template_url=None,
            parameters=None, notification_arns=None, disable_rollback=None,
            timeout_in_minutes=None, capabilities=None, tags=None,
            on_failure=None, stack_policy_body=None, stack_policy_url=None):
        """
        Creates a stack as specified in the template. After the call
        completes successfully, the stack creation starts. You can
        check the status of the stack via the DescribeStacks API.
        Currently, the limit for stacks is 20 stacks per account per
        region.

        :type stack_name: string
        :param stack_name:
        The name associated with the stack. The name must be unique within your
            AWS account.

        Must contain only alphanumeric characters (case sensitive) and start
            with an alpha character. Maximum length of the name is 255
            characters.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateBody` or `TemplateURL`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to the `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type parameters: list
        :param parameters: A list of key/value tuples that specify input
            parameters for the stack.

        :type disable_rollback: boolean
        :param disable_rollback: Set to `True` to disable rollback of the stack
            if stack creation failed. You can specify either `DisableRollback`
            or `OnFailure`, but not both.
        Default: `False`

        :type timeout_in_minutes: integer
        :param timeout_in_minutes: The amount of time that can pass before the
            stack status becomes CREATE_FAILED; if `DisableRollback` is not set
            or is set to `False`, the stack will be rolled back.

        :type notification_arns: list
        :param notification_arns: The Simple Notification Service (SNS) topic
            ARNs to publish stack related events. You can find your SNS topic
            ARNs using the `SNS console`_ or your Command Line Interface (CLI).

        :type capabilities: list
        :param capabilities: The list of capabilities that you want to allow in
            the stack. If your template contains certain resources, you must
            specify the CAPABILITY_IAM value for this parameter; otherwise,
            this action returns an InsufficientCapabilities error. The
            following resources require you to specify the capabilities
            parameter: `AWS::CloudFormation::Stack`_, `AWS::IAM::AccessKey`_,
            `AWS::IAM::Group`_, `AWS::IAM::InstanceProfile`_,
            `AWS::IAM::Policy`_, `AWS::IAM::Role`_, `AWS::IAM::User`_, and
            `AWS::IAM::UserToGroupAddition`_.

        :type on_failure: string
        :param on_failure: Determines what action will be taken if stack
            creation fails. This must be one of: DO_NOTHING, ROLLBACK, or
            DELETE. You can specify either `OnFailure` or `DisableRollback`,
            but not both.
        Default: `ROLLBACK`

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the stack policy body.
            (For more information, go to ` Prevent Updates to Stack Resources`_
            in the AWS CloudFormation User Guide.)
        If you pass `StackPolicyBody` and `StackPolicyURL`, only
            `StackPolicyBody` is used.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the stack
            policy. The URL must point to a policy (max size: 16KB) located in
            an S3 bucket in the same region as the stack. If you pass
            `StackPolicyBody` and `StackPolicyURL`, only `StackPolicyBody` is
            used.

        :type tags: dict
        :param tags: A set of user-defined `Tags` to associate with this stack,
            represented by key/value pairs. Tags defined for the stack are
            propagated to EC2 resources that are created as part of the stack.
            A maximum number of 10 tags can be specified.
        """
        params = self._build_create_or_update_params(stack_name, template_body,
            template_url, parameters, disable_rollback, timeout_in_minutes,
            notification_arns, capabilities, on_failure, stack_policy_body,
            stack_policy_url, tags)
        body = self._do_request('CreateStack', params, '/', 'POST')
        return body['CreateStackResponse']['CreateStackResult']['StackId']

    def update_stack(self, stack_name, template_body=None, template_url=None,
            parameters=None, notification_arns=None, disable_rollback=False,
            timeout_in_minutes=None, capabilities=None, tags=None,
            use_previous_template=None,
            stack_policy_during_update_body=None,
            stack_policy_during_update_url=None,
            stack_policy_body=None, stack_policy_url=None):
        """
        Updates a stack as specified in the template. After the call
        completes successfully, the stack update starts. You can check
        the status of the stack via the DescribeStacks action.



        **Note: **You cannot update `AWS::S3::Bucket`_ resources, for
        example, to add or modify tags.



        To get a copy of the template for an existing stack, you can
        use the GetTemplate action.

        Tags that were associated with this stack during creation time
        will still be associated with the stack after an `UpdateStack`
        operation.

        For more information about creating an update template,
        updating a stack, and monitoring the progress of the update,
        see `Updating a Stack`_.

        :type stack_name: string
        :param stack_name:
        The name or stack ID of the stack to update.

        Must contain only alphanumeric characters (case sensitive) and start
            with an alpha character. Maximum length of the name is 255
            characters.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`. If both `TemplateBody` and
            `TemplateUrl` are passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to the `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`. If both `TemplateBody` and
            `TemplateUrl` are passed, only `TemplateBody` is used.
            `TemplateBody`.

        :type use_previous_template: boolean
        :param use_previous_template: Set to `True` to use the previous
            template instead of uploading a new one via `TemplateBody` or
            `TemplateURL`.
        Conditional: You must pass either `UsePreviousTemplate` or one of
            `TemplateBody` or `TemplateUrl`.

        :type parameters: list
        :param parameters: A list of key/value tuples that specify input
            parameters for the stack. A 3-tuple (key, value, bool) may be used to
            specify the `UsePreviousValue` option.

        :type notification_arns: list
        :param notification_arns: The Simple Notification Service (SNS) topic
            ARNs to publish stack related events. You can find your SNS topic
            ARNs using the `SNS console`_ or your Command Line Interface (CLI).

        :type disable_rollback: bool
        :param disable_rollback: Indicates whether or not to rollback on
            failure.

        :type timeout_in_minutes: integer
        :param timeout_in_minutes: The amount of time that can pass before the
            stack status becomes CREATE_FAILED; if `DisableRollback` is not set
            or is set to `False`, the stack will be rolled back.

        :type capabilities: list
        :param capabilities: The list of capabilities you want to allow in
            the stack.  Currently, the only valid capability is
            'CAPABILITY_IAM'.

        :type tags: dict
        :param tags: A set of user-defined `Tags` to associate with this stack,
            represented by key/value pairs. Tags defined for the stack are
            propagated to EC2 resources that are created as part of the stack.
            A maximum number of 10 tags can be specified.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template located in an S3 bucket in the same
            region as the stack. For more information, go to `Template
            Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type stack_policy_during_update_body: string
        :param stack_policy_during_update_body: Structure containing the
            temporary overriding stack policy body. If you pass
            `StackPolicyDuringUpdateBody` and `StackPolicyDuringUpdateURL`,
            only `StackPolicyDuringUpdateBody` is used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that associated with the stack
            will be used.

        :type stack_policy_during_update_url: string
        :param stack_policy_during_update_url: Location of a file containing
            the temporary overriding stack policy. The URL must point to a
            policy (max size: 16KB) located in an S3 bucket in the same region
            as the stack. If you pass `StackPolicyDuringUpdateBody` and
            `StackPolicyDuringUpdateURL`, only `StackPolicyDuringUpdateBody` is
            used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that is associated with the stack
            will be used.

        :rtype: string
        :return: The unique Stack ID.
        """
        params = self._build_create_or_update_params(stack_name, template_body,
            template_url, parameters, disable_rollback, timeout_in_minutes,
            notification_arns, capabilities, None, stack_policy_body,
            stack_policy_url, tags, use_previous_template,
            stack_policy_during_update_body, stack_policy_during_update_url)
        body = self._do_request('UpdateStack', params, '/', 'POST')
        return body['UpdateStackResponse']['UpdateStackResult']['StackId']

    def delete_stack(self, stack_name_or_id):
        """
        Deletes a specified stack. Once the call completes
        successfully, stack deletion starts. Deleted stacks do not
        show up in the DescribeStacks API if the deletion has been
        completed successfully.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack.

        """
        params = {'ContentType': "JSON", 'StackName': stack_name_or_id}
        return self._do_request('DeleteStack', params, '/', 'GET')

    def describe_stack_events(self, stack_name_or_id=None, next_token=None):
        """
        Returns all stack related events for a specified stack. For
        more information about a stack's event history, go to
        `Stacks`_ in the AWS CloudFormation User Guide.
        Events are returned, even if the stack never existed or has
        been successfully deleted.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack.
        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            events, if there is one.
        Default: There is no default value.

        """
        params = {}
        if stack_name_or_id:
            params['StackName'] = stack_name_or_id
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeStackEvents', params, [('member',
            StackEvent)])

    def describe_stack_resource(self, stack_name_or_id, logical_resource_id):
        """
        Returns a description of the specified resource in the
        specified stack.

        For deleted stacks, DescribeStackResource returns resource
        information for up to 90 days after the stack has been
        deleted.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack.
        Default: There is no default value.

        :type logical_resource_id: string
        :param logical_resource_id: The logical name of the resource as
            specified in the template.
        Default: There is no default value.

        """
        params = {'ContentType': "JSON", 'StackName': stack_name_or_id,
                'LogicalResourceId': logical_resource_id}
        return self._do_request('DescribeStackResource', params, '/', 'GET')

    def describe_stack_resources(self, stack_name_or_id=None,
            logical_resource_id=None,
            physical_resource_id=None):
        """
        Returns AWS resource descriptions for running and deleted
        stacks. If `StackName` is specified, all the associated
        resources that are part of the stack are returned. If
        `PhysicalResourceId` is specified, the associated resources of
        the stack that the resource belongs to are returned.
        Only the first 100 resources will be returned. If your stack
        has more resources than this, you should use
        `ListStackResources` instead.
        For deleted stacks, `DescribeStackResources` returns resource
        information for up to 90 days after the stack has been
        deleted.

        You must specify either `StackName` or `PhysicalResourceId`,
        but not both. In addition, you can specify `LogicalResourceId`
        to filter the returned result. For more information about
        resources, the `LogicalResourceId` and `PhysicalResourceId`,
        go to the `AWS CloudFormation User Guide`_.
        A `ValidationError` is returned if you specify both
        `StackName` and `PhysicalResourceId` in the same request.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack.
        Required: Conditional. If you do not specify `StackName`, you must
            specify `PhysicalResourceId`.

        Default: There is no default value.

        :type logical_resource_id: string
        :param logical_resource_id: The logical name of the resource as
            specified in the template.
        Default: There is no default value.

        :type physical_resource_id: string
        :param physical_resource_id: The name or unique identifier that
            corresponds to a physical instance ID of a resource supported by
            AWS CloudFormation.
        For example, for an Amazon Elastic Compute Cloud (EC2) instance,
            `PhysicalResourceId` corresponds to the `InstanceId`. You can pass
            the EC2 `InstanceId` to `DescribeStackResources` to find which
            stack the instance belongs to and what other resources are part of
            the stack.

        Required: Conditional. If you do not specify `PhysicalResourceId`, you
            must specify `StackName`.

        Default: There is no default value.

        """
        params = {}
        if stack_name_or_id:
            params['StackName'] = stack_name_or_id
        if logical_resource_id:
            params['LogicalResourceId'] = logical_resource_id
        if physical_resource_id:
            params['PhysicalResourceId'] = physical_resource_id
        return self.get_list('DescribeStackResources', params,
                             [('member', StackResource)])

    def describe_stacks(self, stack_name_or_id=None, next_token=None):
        """
        Returns the description for the specified stack; if no stack
        name was specified, then it returns the description for all
        the stacks created.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack.
        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stacks, if there is one.

        """
        params = {}
        if stack_name_or_id:
            params['StackName'] = stack_name_or_id
        if next_token is not None:
            params['NextToken'] = next_token
        return self.get_list('DescribeStacks', params, [('member', Stack)])

    def get_template(self, stack_name_or_id):
        """
        Returns the template body for a specified stack. You can get
        the template for running or deleted stacks.

        For deleted stacks, GetTemplate returns the template for up to
        90 days after the stack has been deleted.
        If the template does not exist, a `ValidationError` is
        returned.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack, which are not always interchangeable:

        + Running stacks: You can specify either the stack's name or its unique
              stack ID.
        + Deleted stacks: You must specify the unique stack ID.


        Default: There is no default value.

        """
        params = {'ContentType': "JSON", 'StackName': stack_name_or_id}
        return self._do_request('GetTemplate', params, '/', 'GET')

    def list_stack_resources(self, stack_name_or_id, next_token=None):
        """
        Returns descriptions of all resources of the specified stack.

        For deleted stacks, ListStackResources returns resource
        information for up to 90 days after the stack has been
        deleted.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated
            with the stack, which are not always interchangeable:

        + Running stacks: You can specify either the stack's name or its unique
              stack ID.
        + Deleted stacks: You must specify the unique stack ID.


        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stack resource summaries, if there is one.
        Default: There is no default value.

        """
        params = {'StackName': stack_name_or_id}
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('ListStackResources', params,
                             [('member', StackResourceSummary)])

    def list_stacks(self, stack_status_filters=None, next_token=None):
        """
        Returns the summary information for stacks whose status
        matches the specified StackStatusFilter. Summary information
        for stacks that have been deleted is kept for 90 days after
        the stack is deleted. If no StackStatusFilter is specified,
        summary information for all stacks is returned (including
        existing stacks and stacks that have been deleted).

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stacks, if there is one.
        Default: There is no default value.

        :type stack_status_filter: list
        :param stack_status_filter: Stack status to use as a filter. Specify
            one or more stack status codes to list only stacks with the
            specified status codes. For a complete list of stack status codes,
            see the `StackStatus` parameter of the Stack data type.

        """
        params = {}
        if next_token:
            params['NextToken'] = next_token
        if stack_status_filters and len(stack_status_filters) > 0:
            self.build_list_params(params, stack_status_filters,
                "StackStatusFilter.member")

        return self.get_list('ListStacks', params,
                             [('member', StackSummary)])

    def validate_template(self, template_body=None, template_url=None):
        """
        Validates a specified template.

        :type template_body: string
        :param template_body: String containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        """
        params = {}
        if template_body:
            params['TemplateBody'] = template_body
        if template_url:
            params['TemplateURL'] = template_url
        if template_body and template_url:
            boto.log.warning("If both TemplateBody and TemplateURL are"
                " specified, only TemplateBody will be honored by the API")
        return self.get_object('ValidateTemplate', params, Template,
                verb="POST")

    def cancel_update_stack(self, stack_name_or_id=None):
        """
        Cancels an update on the specified stack. If the call
        completes successfully, the stack will roll back the update
        and revert to the previous stack configuration.
        Only stacks that are in the UPDATE_IN_PROGRESS state can be
        canceled.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or the unique identifier associated with
            the stack.

        """
        params = {}
        if stack_name_or_id:
            params['StackName'] = stack_name_or_id
        return self.get_status('CancelUpdateStack', params)

    def estimate_template_cost(self, template_body=None, template_url=None,
                               parameters=None):
        """
        Returns the estimated monthly cost of a template. The return
        value is an AWS Simple Monthly Calculator URL with a query
        string that describes the resources required to run the
        template.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateBody` or `TemplateURL`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template located in an S3 bucket in the same
            region as the stack. For more information, go to `Template
            Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type parameters: list
        :param parameters: A list of key/value tuples that specify input
            parameters for the template.

        :rtype: string
        :returns: URL to pre-filled cost calculator
        """
        params = {'ContentType': "JSON"}
        if template_body is not None:
            params['TemplateBody'] = template_body
        if template_url is not None:
            params['TemplateURL'] = template_url
        if parameters and len(parameters) > 0:
            for i, (key, value) in enumerate(parameters):
                params['Parameters.member.%d.ParameterKey' % (i + 1)] = key
                params['Parameters.member.%d.ParameterValue' % (i + 1)] = value

        response = self._do_request('EstimateTemplateCost', params, '/', 'POST')
        return response['EstimateTemplateCostResponse']\
                       ['EstimateTemplateCostResult']\
                       ['Url']

    def get_stack_policy(self, stack_name_or_id):
        """
        Returns the stack policy for a specified stack. If a stack
        doesn't have a policy, a null value is returned.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or stack ID that is associated with
            the stack whose policy you want to get.

        :rtype: string
        :return: The policy JSON document
        """
        params = {'ContentType': "JSON", 'StackName': stack_name_or_id, }
        response = self._do_request('GetStackPolicy', params, '/', 'POST')
        return response['GetStackPolicyResponse']\
                       ['GetStackPolicyResult']\
                       ['StackPolicyBody']

    def set_stack_policy(self, stack_name_or_id, stack_policy_body=None,
                         stack_policy_url=None):
        """
        Sets a stack policy for a specified stack.

        :type stack_name_or_id: string
        :param stack_name_or_id: The name or stack ID that you want to
            associate a policy with.

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the stack policy body.
            (For more information, go to ` Prevent Updates to Stack Resources`_
            in the AWS CloudFormation User Guide.)
        You must pass `StackPolicyBody` or `StackPolicyURL`. If both are
            passed, only `StackPolicyBody` is used.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the stack
            policy. The URL must point to a policy (max size: 16KB) located in
            an S3 bucket in the same region as the stack. You must pass
            `StackPolicyBody` or `StackPolicyURL`. If both are passed, only
            `StackPolicyBody` is used.

        """
        params = {'ContentType': "JSON", 'StackName': stack_name_or_id, }
        if stack_policy_body is not None:
            params['StackPolicyBody'] = stack_policy_body
        if stack_policy_url is not None:
            params['StackPolicyURL'] = stack_policy_url

        response = self._do_request('SetStackPolicy', params, '/', 'POST')
        return response['SetStackPolicyResponse']
