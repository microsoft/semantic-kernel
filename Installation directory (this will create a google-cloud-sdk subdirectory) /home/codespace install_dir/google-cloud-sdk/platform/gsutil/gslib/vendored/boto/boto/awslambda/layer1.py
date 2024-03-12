# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import os

from boto.compat import json
from boto.exception import JSONResponseError
from boto.connection import AWSAuthConnection
from boto.regioninfo import RegionInfo
from boto.awslambda import exceptions


class AWSLambdaConnection(AWSAuthConnection):
    """
    AWS Lambda
    **Overview**

    This is the AWS Lambda API Reference. The AWS Lambda Developer
    Guide provides additional information. For the service overview,
    go to `What is AWS Lambda`_, and for information about how the
    service works, go to `AWS LambdaL How it Works`_ in the AWS Lambda
    Developer Guide.
    """
    APIVersion = "2014-11-11"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "lambda.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidRequestContentException": exceptions.InvalidRequestContentException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InvalidParameterValueException": exceptions.InvalidParameterValueException,
        "ServiceException": exceptions.ServiceException,
    }


    def __init__(self, **kwargs):
        region = kwargs.get('region')
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        else:
            del kwargs['region']
        kwargs['host'] = region.endpoint
        super(AWSLambdaConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_event_source(self, event_source, function_name, role,
                         batch_size=None, parameters=None):
        """
        Identifies an Amazon Kinesis stream as the event source for an
        AWS Lambda function. AWS Lambda invokes the specified function
        when records are posted to the stream.

        This is the pull model, where AWS Lambda invokes the function.
        For more information, go to `AWS LambdaL How it Works`_ in the
        AWS Lambda Developer Guide.

        This association between an Amazon Kinesis stream and an AWS
        Lambda function is called the event source mapping. You
        provide the configuration information (for example, which
        stream to read from and which AWS Lambda function to invoke)
        for the event source mapping in the request body.

        This operation requires permission for the `iam:PassRole`
        action for the IAM role. It also requires permission for the
        `lambda:AddEventSource` action.

        :type event_source: string
        :param event_source: The Amazon Resource Name (ARN) of the Amazon
            Kinesis stream that is the event source. Any record added to this
            stream causes AWS Lambda to invoke your Lambda function. AWS Lambda
            POSTs the Amazon Kinesis event, containing records, to your Lambda
            function as JSON.

        :type function_name: string
        :param function_name: The Lambda function to invoke when AWS Lambda
            detects an event on the stream.

        :type role: string
        :param role: The ARN of the IAM role (invocation role) that AWS Lambda
            can assume to read from the stream and invoke the function.

        :type batch_size: integer
        :param batch_size: The largest number of records that AWS Lambda will
            give to your function in a single event. The default is 100
            records.

        :type parameters: map
        :param parameters: A map (key-value pairs) defining the configuration
            for AWS Lambda to use when reading the event source. Currently, AWS
            Lambda supports only the `InitialPositionInStream` key. The valid
            values are: "TRIM_HORIZON" and "LATEST". The default value is
            "TRIM_HORIZON". For more information, go to `ShardIteratorType`_ in
            the Amazon Kinesis Service API Reference.

        """

        uri = '/2014-11-13/event-source-mappings/'
        params = {
            'EventSource': event_source,
            'FunctionName': function_name,
            'Role': role,
        }
        headers = {}
        query_params = {}
        if batch_size is not None:
            params['BatchSize'] = batch_size
        if parameters is not None:
            params['Parameters'] = parameters
        return self.make_request('POST', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers,
                                 params=query_params)

    def delete_function(self, function_name):
        """
        Deletes the specified Lambda function code and configuration.

        This operation requires permission for the
        `lambda:DeleteFunction` action.

        :type function_name: string
        :param function_name: The Lambda function to delete.

        """

        uri = '/2014-11-13/functions/{0}'.format(function_name)
        return self.make_request('DELETE', uri, expected_status=204)

    def get_event_source(self, uuid):
        """
        Returns configuration information for the specified event
        source mapping (see AddEventSource).

        This operation requires permission for the
        `lambda:GetEventSource` action.

        :type uuid: string
        :param uuid: The AWS Lambda assigned ID of the event source mapping.

        """

        uri = '/2014-11-13/event-source-mappings/{0}'.format(uuid)
        return self.make_request('GET', uri, expected_status=200)

    def get_function(self, function_name):
        """
        Returns the configuration information of the Lambda function
        and a presigned URL link to the .zip file you uploaded with
        UploadFunction so you can download the .zip file. Note that
        the URL is valid for up to 10 minutes. The configuration
        information is the same information you provided as parameters
        when uploading the function.

        This operation requires permission for the
        `lambda:GetFunction` action.

        :type function_name: string
        :param function_name: The Lambda function name.

        """

        uri = '/2014-11-13/functions/{0}'.format(function_name)
        return self.make_request('GET', uri, expected_status=200)

    def get_function_configuration(self, function_name):
        """
        Returns the configuration information of the Lambda function.
        This the same information you provided as parameters when
        uploading the function by using UploadFunction.

        This operation requires permission for the
        `lambda:GetFunctionConfiguration` operation.

        :type function_name: string
        :param function_name: The name of the Lambda function for which you
            want to retrieve the configuration information.

        """

        uri = '/2014-11-13/functions/{0}/configuration'.format(function_name)
        return self.make_request('GET', uri, expected_status=200)

    def invoke_async(self, function_name, invoke_args):
        """
        Submits an invocation request to AWS Lambda. Upon receiving
        the request, Lambda executes the specified function
        asynchronously. To see the logs generated by the Lambda
        function execution, see the CloudWatch logs console.

        This operation requires permission for the
        `lambda:InvokeAsync` action.

        :type function_name: string
        :param function_name: The Lambda function name.

        :type invoke_args: blob
        :param invoke_args: JSON that you want to provide to your Lambda
            function as input.

        """
        uri = '/2014-11-13/functions/{0}/invoke-async/'.format(function_name)
        headers = {}
        query_params = {}
        try:
            content_length = str(len(invoke_args))
        except (TypeError, AttributeError):
            # If a file like object is provided and seekable, try to retrieve
            # the file size via fstat.
            try:
                invoke_args.tell()
            except (AttributeError, OSError, IOError):
                raise TypeError(
                    "File-like object passed to parameter "
                    "``invoke_args`` must be seekable."
                )
            content_length = str(os.fstat(invoke_args.fileno()).st_size)
        headers['Content-Length'] = content_length
        return self.make_request('POST', uri, expected_status=202,
                                 data=invoke_args, headers=headers,
                                 params=query_params)

    def list_event_sources(self, event_source_arn=None, function_name=None,
                           marker=None, max_items=None):
        """
        Returns a list of event source mappings. For each mapping, the
        API returns configuration information (see AddEventSource).
        You can optionally specify filters to retrieve specific event
        source mappings.

        This operation requires permission for the
        `lambda:ListEventSources` action.

        :type event_source_arn: string
        :param event_source_arn: The Amazon Resource Name (ARN) of the Amazon
            Kinesis stream.

        :type function_name: string
        :param function_name: The name of the AWS Lambda function.

        :type marker: string
        :param marker: Optional string. An opaque pagination token returned
            from a previous `ListEventSources` operation. If present, specifies
            to continue the list from where the returning call left off.

        :type max_items: integer
        :param max_items: Optional integer. Specifies the maximum number of
            event sources to return in response. This value must be greater
            than 0.

        """

        uri = '/2014-11-13/event-source-mappings/'
        params = {}
        headers = {}
        query_params = {}
        if event_source_arn is not None:
            query_params['EventSource'] = event_source_arn
        if function_name is not None:
            query_params['FunctionName'] = function_name
        if marker is not None:
            query_params['Marker'] = marker
        if max_items is not None:
            query_params['MaxItems'] = max_items
        return self.make_request('GET', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers,
                                 params=query_params)

    def list_functions(self, marker=None, max_items=None):
        """
        Returns a list of your Lambda functions. For each function,
        the response includes the function configuration information.
        You must use GetFunction to retrieve the code for your
        function.

        This operation requires permission for the
        `lambda:ListFunctions` action.

        :type marker: string
        :param marker: Optional string. An opaque pagination token returned
            from a previous `ListFunctions` operation. If present, indicates
            where to continue the listing.

        :type max_items: integer
        :param max_items: Optional integer. Specifies the maximum number of AWS
            Lambda functions to return in response. This parameter value must
            be greater than 0.

        """

        uri = '/2014-11-13/functions/'
        params = {}
        headers = {}
        query_params = {}
        if marker is not None:
            query_params['Marker'] = marker
        if max_items is not None:
            query_params['MaxItems'] = max_items
        return self.make_request('GET', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers,
                                 params=query_params)

    def remove_event_source(self, uuid):
        """
        Removes an event source mapping. This means AWS Lambda will no
        longer invoke the function for events in the associated
        source.

        This operation requires permission for the
        `lambda:RemoveEventSource` action.

        :type uuid: string
        :param uuid: The event source mapping ID.

        """

        uri = '/2014-11-13/event-source-mappings/{0}'.format(uuid)
        return self.make_request('DELETE', uri, expected_status=204)

    def update_function_configuration(self, function_name, role=None,
                                      handler=None, description=None,
                                      timeout=None, memory_size=None):
        """
        Updates the configuration parameters for the specified Lambda
        function by using the values provided in the request. You
        provide only the parameters you want to change. This operation
        must only be used on an existing Lambda function and cannot be
        used to update the function's code.

        This operation requires permission for the
        `lambda:UpdateFunctionConfiguration` action.

        :type function_name: string
        :param function_name: The name of the Lambda function.

        :type role: string
        :param role: The Amazon Resource Name (ARN) of the IAM role that Lambda
            will assume when it executes your function.

        :type handler: string
        :param handler: The function that Lambda calls to begin executing your
            function. For Node.js, it is the module-name.export value in your
            function.

        :type description: string
        :param description: A short user-defined function description. Lambda
            does not use this value. Assign a meaningful description as you see
            fit.

        :type timeout: integer
        :param timeout: The function execution time at which Lambda should
            terminate the function. Because the execution time has cost
            implications, we recommend you set this value based on your
            expected execution time. The default is 3 seconds.

        :type memory_size: integer
        :param memory_size: The amount of memory, in MB, your Lambda function
            is given. Lambda uses this memory size to infer the amount of CPU
            allocated to your function. Your function use-case determines your
            CPU and memory requirements. For example, a database operation
            might need less memory compared to an image processing function.
            The default value is 128 MB. The value must be a multiple of 64 MB.

        """

        uri = '/2014-11-13/functions/{0}/configuration'.format(function_name)
        params = {}
        headers = {}
        query_params = {}
        if role is not None:
            query_params['Role'] = role
        if handler is not None:
            query_params['Handler'] = handler
        if description is not None:
            query_params['Description'] = description
        if timeout is not None:
            query_params['Timeout'] = timeout
        if memory_size is not None:
            query_params['MemorySize'] = memory_size
        return self.make_request('PUT', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers,
                                 params=query_params)

    def upload_function(self, function_name, function_zip, runtime, role,
                        handler, mode, description=None, timeout=None,
                        memory_size=None):
        """
        Creates a new Lambda function or updates an existing function.
        The function metadata is created from the request parameters,
        and the code for the function is provided by a .zip file in
        the request body. If the function name already exists, the
        existing Lambda function is updated with the new code and
        metadata.

        This operation requires permission for the
        `lambda:UploadFunction` action.

        :type function_name: string
        :param function_name: The name you want to assign to the function you
            are uploading. The function names appear in the console and are
            returned in the ListFunctions API. Function names are used to
            specify functions to other AWS Lambda APIs, such as InvokeAsync.

        :type function_zip: blob
        :param function_zip: A .zip file containing your packaged source code.
            For more information about creating a .zip file, go to `AWS LambdaL
            How it Works`_ in the AWS Lambda Developer Guide.

        :type runtime: string
        :param runtime: The runtime environment for the Lambda function you are
            uploading. Currently, Lambda supports only "nodejs" as the runtime.

        :type role: string
        :param role: The Amazon Resource Name (ARN) of the IAM role that Lambda
            assumes when it executes your function to access any other Amazon
            Web Services (AWS) resources.

        :type handler: string
        :param handler: The function that Lambda calls to begin execution. For
            Node.js, it is the module-name . export value in your function.

        :type mode: string
        :param mode: How the Lambda function will be invoked. Lambda supports
            only the "event" mode.

        :type description: string
        :param description: A short, user-defined function description. Lambda
            does not use this value. Assign a meaningful description as you see
            fit.

        :type timeout: integer
        :param timeout: The function execution time at which Lambda should
            terminate the function. Because the execution time has cost
            implications, we recommend you set this value based on your
            expected execution time. The default is 3 seconds.

        :type memory_size: integer
        :param memory_size: The amount of memory, in MB, your Lambda function
            is given. Lambda uses this memory size to infer the amount of CPU
            allocated to your function. Your function use-case determines your
            CPU and memory requirements. For example, database operation might
            need less memory compared to image processing function. The default
            value is 128 MB. The value must be a multiple of 64 MB.

        """
        uri = '/2014-11-13/functions/{0}'.format(function_name)
        headers = {}
        query_params = {}
        if runtime is not None:
            query_params['Runtime'] = runtime
        if role is not None:
            query_params['Role'] = role
        if handler is not None:
            query_params['Handler'] = handler
        if mode is not None:
            query_params['Mode'] = mode
        if description is not None:
            query_params['Description'] = description
        if timeout is not None:
            query_params['Timeout'] = timeout
        if memory_size is not None:
            query_params['MemorySize'] = memory_size

        try:
            content_length = str(len(function_zip))
        except (TypeError, AttributeError):
            # If a file like object is provided and seekable, try to retrieve
            # the file size via fstat.
            try:
                function_zip.tell()
            except (AttributeError, OSError, IOError):
                raise TypeError(
                    "File-like object passed to parameter "
                    "``function_zip`` must be seekable."
                )
            content_length = str(os.fstat(function_zip.fileno()).st_size)
        headers['Content-Length'] = content_length
        return self.make_request('PUT', uri, expected_status=201,
                                 data=function_zip, headers=headers,
                                 params=query_params)

    def make_request(self, verb, resource, headers=None, data='',
                     expected_status=None, params=None):
        if headers is None:
            headers = {}
        response = AWSAuthConnection.make_request(
            self, verb, resource, headers=headers, data=data, params=params)
        body = response.read().decode('utf-8')
        if body:
            body = json.loads(body)
        if response.status == expected_status:
            return body
        else:
            error_type = response.getheader('x-amzn-ErrorType').split(':')[0]
            error_class = self._faults.get(error_type, self.ResponseError)
            raise error_class(response.status, response.reason, body)
