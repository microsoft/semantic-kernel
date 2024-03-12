# -*- coding: utf-8 -*-
# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import boto.glacier
from boto.compat import json
from boto.connection import AWSAuthConnection
from boto.glacier.exceptions import UnexpectedHTTPResponseError
from boto.glacier.response import GlacierResponse
from boto.glacier.utils import ResettingFileSender


class Layer1(AWSAuthConnection):
    """
    Amazon Glacier is a storage solution for "cold data."

    Amazon Glacier is an extremely low-cost storage service that
    provides secure, durable and easy-to-use storage for data backup
    and archival. With Amazon Glacier, customers can store their data
    cost effectively for months, years, or decades. Amazon Glacier
    also enables customers to offload the administrative burdens of
    operating and scaling storage to AWS, so they don't have to worry
    about capacity planning, hardware provisioning, data replication,
    hardware failure and recovery, or time-consuming hardware
    migrations.

    Amazon Glacier is a great storage choice when low storage cost is
    paramount, your data is rarely retrieved, and retrieval latency of
    several hours is acceptable. If your application requires fast or
    frequent access to your data, consider using Amazon S3. For more
    information, go to `Amazon Simple Storage Service (Amazon S3)`_.

    You can store any kind of data in any format. There is no maximum
    limit on the total amount of data you can store in Amazon Glacier.

    If you are a first-time user of Amazon Glacier, we recommend that
    you begin by reading the following sections in the Amazon Glacier
    Developer Guide :


    + `What is Amazon Glacier`_ - This section of the Developer Guide
      describes the underlying data model, the operations it supports,
      and the AWS SDKs that you can use to interact with the service.
    + `Getting Started with Amazon Glacier`_ - The Getting Started
      section walks you through the process of creating a vault,
      uploading archives, creating jobs to download archives, retrieving
      the job output, and deleting archives.
      """
    Version = '2012-06-01'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 account_id='-', is_secure=True, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, path='/',
                 provider='aws', security_token=None,
                 suppress_consec_slashes=True,
                 region=None, region_name='us-east-1',
                 profile_name=None):

        if not region:
            for reg in boto.glacier.regions():
                if reg.name == region_name:
                    region = reg
                    break

        self.region = region
        self.account_id = account_id
        super(Layer1, self).__init__(region.endpoint,
                                     aws_access_key_id, aws_secret_access_key,
                                     is_secure, port, proxy, proxy_port,
                                     proxy_user, proxy_pass, debug,
                                     https_connection_factory,
                                     path, provider, security_token,
                                     suppress_consec_slashes,
                                     profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def make_request(self, verb, resource, headers=None,
                     data='', ok_responses=(200,), params=None,
                     sender=None, response_headers=None):
        if headers is None:
            headers = {}
        headers['x-amz-glacier-version'] = self.Version
        uri = '/%s/%s' % (self.account_id, resource)
        response = super(Layer1, self).make_request(verb, uri,
                                                    params=params,
                                                    headers=headers,
                                                    sender=sender,
                                                    data=data)
        if response.status in ok_responses:
            return GlacierResponse(response, response_headers)
        else:
            # create glacier-specific exceptions
            raise UnexpectedHTTPResponseError(ok_responses, response)

    # Vaults

    def list_vaults(self, limit=None, marker=None):
        """
        This operation lists all vaults owned by the calling user's
        account. The list returned in the response is ASCII-sorted by
        vault name.

        By default, this operation returns up to 1,000 items. If there
        are more vaults to list, the response `marker` field contains
        the vault Amazon Resource Name (ARN) at which to continue the
        list with a new List Vaults request; otherwise, the `marker`
        field is `null`. To return a list of vaults that begins at a
        specific vault, set the `marker` request parameter to the
        vault ARN you obtained from a previous List Vaults request.
        You can also limit the number of vaults returned in the
        response by specifying the `limit` parameter in the request.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Retrieving Vault Metadata in Amazon Glacier`_ and `List
        Vaults `_ in the Amazon Glacier Developer Guide .

        :type marker: string
        :param marker: A string used for pagination. The marker specifies the
            vault ARN after which the listing of vaults should begin.

        :type limit: string
        :param limit: The maximum number of items returned in the response. If
            you don't specify a value, the List Vaults operation returns up to
            1,000 items.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        return self.make_request('GET', 'vaults', params=params)

    def describe_vault(self, vault_name):
        """
        This operation returns information about a vault, including
        the vault's Amazon Resource Name (ARN), the date the vault was
        created, the number of archives it contains, and the total
        size of all the archives in the vault. The number of archives
        and their total size are as of the last inventory generation.
        This means that if you add or remove an archive from a vault,
        and then immediately use Describe Vault, the change in
        contents will not be immediately reflected. If you want to
        retrieve the latest inventory of the vault, use InitiateJob.
        Amazon Glacier generates vault inventories approximately
        daily. For more information, see `Downloading a Vault
        Inventory in Amazon Glacier`_.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Retrieving Vault Metadata in Amazon Glacier`_ and `Describe
        Vault `_ in the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('GET', uri)

    def create_vault(self, vault_name):
        """
        This operation creates a new vault with the specified name.
        The name of the vault must be unique within a region for an
        AWS account. You can create up to 1,000 vaults per account. If
        you need to create more vaults, contact Amazon Glacier.

        You must use the following guidelines when naming a vault.



        + Names can be between 1 and 255 characters long.
        + Allowed characters are a-z, A-Z, 0-9, '_' (underscore), '-'
          (hyphen), and '.' (period).



        This operation is idempotent.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Creating a Vault in Amazon Glacier`_ and `Create Vault `_ in
        the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('PUT', uri, ok_responses=(201,),
                                 response_headers=[('Location', 'Location')])

    def delete_vault(self, vault_name):
        """
        This operation deletes a vault. Amazon Glacier will delete a
        vault only if there are no archives in the vault as of the
        last inventory and there have been no writes to the vault
        since the last inventory. If either of these conditions is not
        satisfied, the vault deletion fails (that is, the vault is not
        removed) and Amazon Glacier returns an error. You can use
        DescribeVault to return the number of archives in a vault, and
        you can use `Initiate a Job (POST jobs)`_ to initiate a new
        inventory retrieval for a vault. The inventory contains the
        archive IDs you use to delete archives using `Delete Archive
        (DELETE archive)`_.

        This operation is idempotent.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Deleting a Vault in Amazon Glacier`_ and `Delete Vault `_ in
        the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('DELETE', uri, ok_responses=(204,))

    def get_vault_notifications(self, vault_name):
        """
        This operation retrieves the `notification-configuration`
        subresource of the specified vault.

        For information about setting a notification configuration on
        a vault, see SetVaultNotifications. If a notification
        configuration for a vault is not set, the operation returns a
        `404 Not Found` error. For more information about vault
        notifications, see `Configuring Vault Notifications in Amazon
        Glacier`_.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Configuring Vault Notifications in Amazon Glacier`_ and `Get
        Vault Notification Configuration `_ in the Amazon Glacier
        Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        return self.make_request('GET', uri)

    def set_vault_notifications(self, vault_name, notification_config):
        """
        This operation configures notifications that will be sent when
        specific events happen to a vault. By default, you don't get
        any notifications.

        To configure vault notifications, send a PUT request to the
        `notification-configuration` subresource of the vault. The
        request should include a JSON document that provides an Amazon
        SNS topic and specific events for which you want Amazon
        Glacier to send notifications to the topic.

        Amazon SNS topics must grant permission to the vault to be
        allowed to publish notifications to the topic. You can
        configure a vault to publish a notification for the following
        vault events:


        + **ArchiveRetrievalCompleted** This event occurs when a job
          that was initiated for an archive retrieval is completed
          (InitiateJob). The status of the completed job can be
          "Succeeded" or "Failed". The notification sent to the SNS
          topic is the same output as returned from DescribeJob.
        + **InventoryRetrievalCompleted** This event occurs when a job
          that was initiated for an inventory retrieval is completed
          (InitiateJob). The status of the completed job can be
          "Succeeded" or "Failed". The notification sent to the SNS
          topic is the same output as returned from DescribeJob.


        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Configuring Vault Notifications in Amazon Glacier`_ and `Set
        Vault Notification Configuration `_ in the Amazon Glacier
        Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type vault_notification_config: dict
        :param vault_notification_config: Provides options for specifying
            notification configuration.

            The format of the dictionary is:

                {'SNSTopic': 'mytopic',
                 'Events': [event1,...]}
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        json_config = json.dumps(notification_config)
        return self.make_request('PUT', uri, data=json_config,
                                 ok_responses=(204,))

    def delete_vault_notifications(self, vault_name):
        """
        This operation deletes the notification configuration set for
        a vault. The operation is eventually consistent;that is, it
        might take some time for Amazon Glacier to completely disable
        the notifications and you might still receive some
        notifications for a short time after you send the delete
        request.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Configuring Vault Notifications in Amazon Glacier`_ and
        `Delete Vault Notification Configuration `_ in the Amazon
        Glacier Developer Guide.

        :type vault_name: string
        :param vault_name: The name of the vault.
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        return self.make_request('DELETE', uri, ok_responses=(204,))

    # Jobs

    def list_jobs(self, vault_name, completed=None, status_code=None,
                  limit=None, marker=None):
        """
        This operation lists jobs for a vault, including jobs that are
        in-progress and jobs that have recently finished.


        Amazon Glacier retains recently completed jobs for a period
        before deleting them; however, it eventually removes completed
        jobs. The output of completed jobs can be retrieved. Retaining
        completed jobs for a period of time after they have completed
        enables you to get a job output in the event you miss the job
        completion notification or your first attempt to download it
        fails. For example, suppose you start an archive retrieval job
        to download an archive. After the job completes, you start to
        download the archive but encounter a network error. In this
        scenario, you can retry and download the archive while the job
        exists.


        To retrieve an archive or retrieve a vault inventory from
        Amazon Glacier, you first initiate a job, and after the job
        completes, you download the data. For an archive retrieval,
        the output is the archive data, and for an inventory
        retrieval, it is the inventory list. The List Job operation
        returns a list of these jobs sorted by job initiation time.

        This List Jobs operation supports pagination. By default, this
        operation returns up to 1,000 jobs in the response. You should
        always check the response for a `marker` at which to continue
        the list; if there are no more items the `marker` is `null`.
        To return a list of jobs that begins at a specific job, set
        the `marker` request parameter to the value you obtained from
        a previous List Jobs request. You can also limit the number of
        jobs returned in the response by specifying the `limit`
        parameter in the request.

        Additionally, you can filter the jobs list returned by
        specifying an optional `statuscode` (InProgress, Succeeded, or
        Failed) and `completed` (true, false) parameter. The
        `statuscode` allows you to specify that only jobs that match a
        specified status are returned. The `completed` parameter
        allows you to specify that only jobs in a specific completion
        state are returned.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For the underlying REST API, go to `List Jobs `_

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type limit: string
        :param limit: Specifies that the response be limited to the specified
            number of items or fewer. If not specified, the List Jobs operation
            returns up to 1,000 jobs.

        :type marker: string
        :param marker: An opaque string used for pagination. This value
            specifies the job at which the listing of jobs should begin. Get
            the marker value from a previous List Jobs response. You need only
            include the marker if you are continuing the pagination of results
            started in a previous List Jobs request.

        :type statuscode: string
        :param statuscode: Specifies the type of job status to return. You can
            specify the following values: "InProgress", "Succeeded", or
            "Failed".

        :type completed: string
        :param completed: Specifies the state of the jobs to return. You can
            specify `True` or `False`.

        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        if status_code:
            params['statuscode'] = status_code
        if completed is not None:
            params['completed'] = 'true' if completed else 'false'
        uri = 'vaults/%s/jobs' % vault_name
        return self.make_request('GET', uri, params=params)

    def describe_job(self, vault_name, job_id):
        """
        This operation returns information about a job you previously
        initiated, including the job initiation date, the user who
        initiated the job, the job status code/message and the Amazon
        SNS topic to notify after Amazon Glacier completes the job.
        For more information about initiating a job, see InitiateJob.


        This operation enables you to check the status of your job.
        However, it is strongly recommended that you set up an Amazon
        SNS topic and specify it in your initiate job request so that
        Amazon Glacier can notify the topic after it completes the
        job.


        A job ID will not expire for at least 24 hours after Amazon
        Glacier completes the job.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For information about the underlying REST API, go to `Working
        with Archives in Amazon Glacier`_ in the Amazon Glacier
        Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type job_id: string
        :param job_id: The ID of the job to describe.
        """
        uri = 'vaults/%s/jobs/%s' % (vault_name, job_id)
        return self.make_request('GET', uri, ok_responses=(200,))

    def initiate_job(self, vault_name, job_data):
        """
        This operation initiates a job of the specified type. In this
        release, you can initiate a job to retrieve either an archive
        or a vault inventory (a list of archives in a vault).

        Retrieving data from Amazon Glacier is a two-step process:


        #. Initiate a retrieval job.
        #. After the job completes, download the bytes.


        The retrieval request is executed asynchronously. When you
        initiate a retrieval job, Amazon Glacier creates a job and
        returns a job ID in the response. When Amazon Glacier
        completes the job, you can get the job output (archive or
        inventory data). For information about getting job output, see
        GetJobOutput operation.

        The job must complete before you can get its output. To
        determine when a job is complete, you have the following
        options:


        + **Use Amazon SNS Notification** You can specify an Amazon
          Simple Notification Service (Amazon SNS) topic to which Amazon
          Glacier can post a notification after the job is completed.
          You can specify an SNS topic per job request. The notification
          is sent only after Amazon Glacier completes the job. In
          addition to specifying an SNS topic per job request, you can
          configure vault notifications for a vault so that job
          notifications are always sent. For more information, see
          SetVaultNotifications.
        + **Get job details** You can make a DescribeJob request to
          obtain job status information while a job is in progress.
          However, it is more efficient to use an Amazon SNS
          notification to determine when a job is complete.



        The information you get via notification is same that you get
        by calling DescribeJob.


        If for a specific event, you add both the notification
        configuration on the vault and also specify an SNS topic in
        your initiate job request, Amazon Glacier sends both
        notifications. For more information, see
        SetVaultNotifications.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        **About the Vault Inventory**

        Amazon Glacier prepares an inventory for each vault
        periodically, every 24 hours. When you initiate a job for a
        vault inventory, Amazon Glacier returns the last inventory for
        the vault. The inventory data you get might be up to a day or
        two days old. Also, the initiate inventory job might take some
        time to complete before you can download the vault inventory.
        So you do not want to retrieve a vault inventory for each
        vault operation. However, in some scenarios, you might find
        the vault inventory useful. For example, when you upload an
        archive, you can provide an archive description but not an
        archive name. Amazon Glacier provides you a unique archive ID,
        an opaque string of characters. So, you might maintain your
        own database that maps archive names to their corresponding
        Amazon Glacier assigned archive IDs. You might find the vault
        inventory useful in the event you need to reconcile
        information in your database with the actual vault inventory.

        **About Ranged Archive Retrieval**

        You can initiate an archive retrieval for the whole archive or
        a range of the archive. In the case of ranged archive
        retrieval, you specify a byte range to return or the whole
        archive. The range specified must be megabyte (MB) aligned,
        that is the range start value must be divisible by 1 MB and
        range end value plus 1 must be divisible by 1 MB or equal the
        end of the archive. If the ranged archive retrieval is not
        megabyte aligned, this operation returns a 400 response.
        Furthermore, to ensure you get checksum values for data you
        download using Get Job Output API, the range must be tree hash
        aligned.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and the underlying REST API, go to
        `Initiate a Job`_ and `Downloading a Vault Inventory`_

        :type account_id: string
        :param account_id: The `AccountId` is the AWS Account ID. You can
            specify either the AWS Account ID or optionally a '-', in which
            case Amazon Glacier uses the AWS Account ID associated with the
            credentials used to sign the request. If you specify your Account
            ID, do not include hyphens in it.

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type job_parameters: dict
        :param job_parameters: Provides options for specifying job information.
            The dictionary can contain the following attributes:

            * ArchiveId - The ID of the archive you want to retrieve.
              This field is required only if the Type is set to
              archive-retrieval.
            * Description - The optional description for the job.
            * Format - When initiating a job to retrieve a vault
              inventory, you can optionally add this parameter to
              specify the output format.  Valid values are: CSV|JSON.
            * SNSTopic - The Amazon SNS topic ARN where Amazon Glacier
              sends a notification when the job is completed and the
              output is ready for you to download.
            * Type - The job type.  Valid values are:
              archive-retrieval|inventory-retrieval
            * RetrievalByteRange - Optionally specify the range of
              bytes to retrieve.
            * InventoryRetrievalParameters: Optional job parameters
                * Format - The output format, like "JSON"
                * StartDate - ISO8601 starting date string
                * EndDate - ISO8601 ending date string
                * Limit - Maximum number of entries
                * Marker - A unique string used for pagination

        """
        uri = 'vaults/%s/jobs' % vault_name
        response_headers = [('x-amz-job-id', u'JobId'),
                            ('Location', u'Location')]
        json_job_data = json.dumps(job_data)
        return self.make_request('POST', uri, data=json_job_data,
                                 ok_responses=(202,),
                                 response_headers=response_headers)

    def get_job_output(self, vault_name, job_id, byte_range=None):
        """
        This operation downloads the output of the job you initiated
        using InitiateJob. Depending on the job type you specified
        when you initiated the job, the output will be either the
        content of an archive or a vault inventory.

        A job ID will not expire for at least 24 hours after Amazon
        Glacier completes the job. That is, you can download the job
        output within the 24 hours period after Amazon Glacier
        completes the job.

        If the job output is large, then you can use the `Range`
        request header to retrieve a portion of the output. This
        allows you to download the entire output in smaller chunks of
        bytes. For example, suppose you have 1 GB of job output you
        want to download and you decide to download 128 MB chunks of
        data at a time, which is a total of eight Get Job Output
        requests. You use the following process to download the job
        output:


        #. Download a 128 MB chunk of output by specifying the
           appropriate byte range using the `Range` header.
        #. Along with the data, the response includes a checksum of
           the payload. You compute the checksum of the payload on the
           client and compare it with the checksum you received in the
           response to ensure you received all the expected data.
        #. Repeat steps 1 and 2 for all the eight 128 MB chunks of
           output data, each time specifying the appropriate byte range.
        #. After downloading all the parts of the job output, you have
           a list of eight checksum values. Compute the tree hash of
           these values to find the checksum of the entire output. Using
           the Describe Job API, obtain job information of the job that
           provided you the output. The response includes the checksum of
           the entire archive stored in Amazon Glacier. You compare this
           value with the checksum you computed to ensure you have
           downloaded the entire archive content with no errors.


        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and the underlying REST API, go to
        `Downloading a Vault Inventory`_, `Downloading an Archive`_,
        and `Get Job Output `_

        :type account_id: string
        :param account_id: The `AccountId` is the AWS Account ID. You can
            specify either the AWS Account ID or optionally a '-', in which
            case Amazon Glacier uses the AWS Account ID associated with the
            credentials used to sign the request. If you specify your Account
            ID, do not include hyphens in it.

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type job_id: string
        :param job_id: The job ID whose data is downloaded.

        :type byte_range: string
        :param byte_range: The range of bytes to retrieve from the output. For
            example, if you want to download the first 1,048,576 bytes, specify
            "Range: bytes=0-1048575". By default, this operation downloads the
            entire output.
        """
        response_headers = [('x-amz-sha256-tree-hash', u'TreeHash'),
                            ('Content-Range', u'ContentRange'),
                            ('Content-Type', u'ContentType')]
        headers = None
        if byte_range:
            headers = {'Range': 'bytes=%d-%d' % byte_range}
        uri = 'vaults/%s/jobs/%s/output' % (vault_name, job_id)
        response = self.make_request('GET', uri, headers=headers,
                                     ok_responses=(200, 206),
                                     response_headers=response_headers)
        return response

    # Archives

    def upload_archive(self, vault_name, archive,
                       linear_hash, tree_hash, description=None):
        """
        This operation adds an archive to a vault. This is a
        synchronous operation, and for a successful upload, your data
        is durably persisted. Amazon Glacier returns the archive ID in
        the `x-amz-archive-id` header of the response.

        You must use the archive ID to access your data in Amazon
        Glacier. After you upload an archive, you should save the
        archive ID returned so that you can retrieve or delete the
        archive later. Besides saving the archive ID, you can also
        index it and give it a friendly name to allow for better
        searching. You can also use the optional archive description
        field to specify how the archive is referred to in an external
        index of archives, such as you might create in Amazon
        DynamoDB. You can also get the vault inventory to obtain a
        list of archive IDs in a vault. For more information, see
        InitiateJob.

        You must provide a SHA256 tree hash of the data you are
        uploading. For information about computing a SHA256 tree hash,
        see `Computing Checksums`_.

        You can optionally specify an archive description of up to
        1,024 printable ASCII characters. You can get the archive
        description when you either retrieve the archive or get the
        vault inventory. For more information, see InitiateJob. Amazon
        Glacier does not interpret the description in any way. An
        archive description does not need to be unique. You cannot use
        the description to retrieve or sort the archive list.

        Archives are immutable. After you upload an archive, you
        cannot edit the archive or its description.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Uploading an Archive in Amazon Glacier`_ and `Upload
        Archive`_ in the Amazon Glacier Developer Guide .

        :type vault_name: str
        :param vault_name: The name of the vault

        :type archive: bytes
        :param archive: The data to upload.

        :type linear_hash: str
        :param linear_hash: The SHA256 checksum (a linear hash) of the
            payload.

        :type tree_hash: str
        :param tree_hash: The user-computed SHA256 tree hash of the
            payload.  For more information on computing the
            tree hash, see http://goo.gl/u7chF.

        :type description: str
        :param description: The optional description of the archive you
            are uploading.
        """
        response_headers = [('x-amz-archive-id', u'ArchiveId'),
                            ('Location', u'Location'),
                            ('x-amz-sha256-tree-hash', u'TreeHash')]
        uri = 'vaults/%s/archives' % vault_name
        try:
            content_length = str(len(archive))
        except (TypeError, AttributeError):
            # If a file like object is provided, try to retrieve
            # the file size via fstat.
            content_length = str(os.fstat(archive.fileno()).st_size)
        headers = {'x-amz-content-sha256': linear_hash,
                   'x-amz-sha256-tree-hash': tree_hash,
                   'Content-Length': content_length}
        if description:
            headers['x-amz-archive-description'] = description
        if self._is_file_like(archive):
            sender = ResettingFileSender(archive)
        else:
            sender = None
        return self.make_request('POST', uri, headers=headers,
                                 sender=sender,
                                 data=archive, ok_responses=(201,),
                                 response_headers=response_headers)

    def _is_file_like(self, archive):
        return hasattr(archive, 'seek') and hasattr(archive, 'tell')

    def delete_archive(self, vault_name, archive_id):
        """
        This operation deletes an archive from a vault. Subsequent
        requests to initiate a retrieval of this archive will fail.
        Archive retrievals that are in progress for this archive ID
        may or may not succeed according to the following scenarios:


        + If the archive retrieval job is actively preparing the data
          for download when Amazon Glacier receives the delete archive
          request, the archival retrieval operation might fail.
        + If the archive retrieval job has successfully prepared the
          archive for download when Amazon Glacier receives the delete
          archive request, you will be able to download the output.


        This operation is idempotent. Attempting to delete an already-
        deleted archive does not result in an error.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Deleting an Archive in Amazon Glacier`_ and `Delete Archive`_
        in the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type archive_id: string
        :param archive_id: The ID of the archive to delete.
        """
        uri = 'vaults/%s/archives/%s' % (vault_name, archive_id)
        return self.make_request('DELETE', uri, ok_responses=(204,))

    # Multipart

    def initiate_multipart_upload(self, vault_name, part_size,
                                  description=None):
        """
        This operation initiates a multipart upload. Amazon Glacier
        creates a multipart upload resource and returns its ID in the
        response. The multipart upload ID is used in subsequent
        requests to upload parts of an archive (see
        UploadMultipartPart).

        When you initiate a multipart upload, you specify the part
        size in number of bytes. The part size must be a megabyte
        (1024 KB) multiplied by a power of 2-for example, 1048576 (1
        MB), 2097152 (2 MB), 4194304 (4 MB), 8388608 (8 MB), and so
        on. The minimum allowable part size is 1 MB, and the maximum
        is 4 GB.

        Every part you upload to this resource (see
        UploadMultipartPart), except the last one, must have the same
        size. The last one can be the same size or smaller. For
        example, suppose you want to upload a 16.2 MB file. If you
        initiate the multipart upload with a part size of 4 MB, you
        will upload four parts of 4 MB each and one part of 0.2 MB.


        You don't need to know the size of the archive when you start
        a multipart upload because Amazon Glacier does not require you
        to specify the overall archive size.


        After you complete the multipart upload, Amazon Glacier
        removes the multipart upload resource referenced by the ID.
        Amazon Glacier also removes the multipart upload resource if
        you cancel the multipart upload or it may be removed if there
        is no activity for a period of 24 hours.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Uploading Large Archives in Parts (Multipart Upload)`_ and
        `Initiate Multipart Upload`_ in the Amazon Glacier Developer
        Guide .

        The part size must be a megabyte (1024 KB) multiplied by a power of
        2, for example, 1048576 (1 MB), 2097152 (2 MB), 4194304 (4 MB),
        8388608 (8 MB), and so on. The minimum allowable part size is 1 MB,
        and the maximum is 4 GB (4096 MB).

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type description: str
        :param description: The archive description that you are uploading in
            parts.

        :type part_size: int
        :param part_size: The size of each part except the last, in bytes. The
            last part can be smaller than this part size.
        """
        response_headers = [('x-amz-multipart-upload-id', u'UploadId'),
                            ('Location', u'Location')]
        headers = {'x-amz-part-size': str(part_size)}
        if description:
            headers['x-amz-archive-description'] = description
        uri = 'vaults/%s/multipart-uploads' % vault_name
        response = self.make_request('POST', uri, headers=headers,
                                     ok_responses=(201,),
                                     response_headers=response_headers)
        return response

    def complete_multipart_upload(self, vault_name, upload_id,
                                  sha256_treehash, archive_size):
        """
        You call this operation to inform Amazon Glacier that all the
        archive parts have been uploaded and that Amazon Glacier can
        now assemble the archive from the uploaded parts. After
        assembling and saving the archive to the vault, Amazon Glacier
        returns the URI path of the newly created archive resource.
        Using the URI path, you can then access the archive. After you
        upload an archive, you should save the archive ID returned to
        retrieve the archive at a later point. You can also get the
        vault inventory to obtain a list of archive IDs in a vault.
        For more information, see InitiateJob.

        In the request, you must include the computed SHA256 tree hash
        of the entire archive you have uploaded. For information about
        computing a SHA256 tree hash, see `Computing Checksums`_. On
        the server side, Amazon Glacier also constructs the SHA256
        tree hash of the assembled archive. If the values match,
        Amazon Glacier saves the archive to the vault; otherwise, it
        returns an error, and the operation fails. The ListParts
        operation returns a list of parts uploaded for a specific
        multipart upload. It includes checksum information for each
        uploaded part that can be used to debug a bad checksum issue.

        Additionally, Amazon Glacier also checks for any missing
        content ranges when assembling the archive, if missing content
        ranges are found, Amazon Glacier returns an error and the
        operation fails.

        Complete Multipart Upload is an idempotent operation. After
        your first successful complete multipart upload, if you call
        the operation again within a short period, the operation will
        succeed and return the same archive ID. This is useful in the
        event you experience a network issue that causes an aborted
        connection or receive a 500 server error, in which case you
        can repeat your Complete Multipart Upload request and get the
        same archive ID without creating duplicate archives. Note,
        however, that after the multipart upload completes, you cannot
        call the List Parts operation and the multipart upload will
        not appear in List Multipart Uploads response, even if
        idempotent complete is possible.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Uploading Large Archives in Parts (Multipart Upload)`_ and
        `Complete Multipart Upload`_ in the Amazon Glacier Developer
        Guide .

        :type checksum: string
        :param checksum: The SHA256 tree hash of the entire archive. It is the
            tree hash of SHA256 tree hash of the individual parts. If the value
            you specify in the request does not match the SHA256 tree hash of
            the final assembled archive as computed by Amazon Glacier, Amazon
            Glacier returns an error and the request fails.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type upload_id: str
        :param upload_id: The upload ID of the multipart upload.

        :type sha256_treehash: str
        :param sha256_treehash: The SHA256 tree hash of the entire archive.
            It is the tree hash of SHA256 tree hash of the individual parts.
            If the value you specify in the request does not match the SHA256
            tree hash of the final assembled archive as computed by Amazon
            Glacier, Amazon Glacier returns an error and the request fails.

        :type archive_size: int
        :param archive_size: The total size, in bytes, of the entire
            archive. This value should be the sum of all the sizes of
            the individual parts that you uploaded.
        """
        response_headers = [('x-amz-archive-id', u'ArchiveId'),
                            ('Location', u'Location')]
        headers = {'x-amz-sha256-tree-hash': sha256_treehash,
                   'x-amz-archive-size': str(archive_size)}
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        response = self.make_request('POST', uri, headers=headers,
                                     ok_responses=(201,),
                                     response_headers=response_headers)
        return response

    def abort_multipart_upload(self, vault_name, upload_id):
        """
        This operation aborts a multipart upload identified by the
        upload ID.

        After the Abort Multipart Upload request succeeds, you cannot
        upload any more parts to the multipart upload or complete the
        multipart upload. Aborting a completed upload fails. However,
        aborting an already-aborted upload will succeed, for a short
        time. For more information about uploading a part and
        completing a multipart upload, see UploadMultipartPart and
        CompleteMultipartUpload.

        This operation is idempotent.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Working with Archives in Amazon Glacier`_ and `Abort
        Multipart Upload`_ in the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type upload_id: string
        :param upload_id: The upload ID of the multipart upload to delete.
        """
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        return self.make_request('DELETE', uri, ok_responses=(204,))

    def list_multipart_uploads(self, vault_name, limit=None, marker=None):
        """
        This operation lists in-progress multipart uploads for the
        specified vault. An in-progress multipart upload is a
        multipart upload that has been initiated by an
        InitiateMultipartUpload request, but has not yet been
        completed or aborted. The list returned in the List Multipart
        Upload response has no guaranteed order.

        The List Multipart Uploads operation supports pagination. By
        default, this operation returns up to 1,000 multipart uploads
        in the response. You should always check the response for a
        `marker` at which to continue the list; if there are no more
        items the `marker` is `null`. To return a list of multipart
        uploads that begins at a specific upload, set the `marker`
        request parameter to the value you obtained from a previous
        List Multipart Upload request. You can also limit the number
        of uploads returned in the response by specifying the `limit`
        parameter in the request.

        Note the difference between this operation and listing parts
        (ListParts). The List Multipart Uploads operation lists all
        multipart uploads for a vault and does not require a multipart
        upload ID. The List Parts operation requires a multipart
        upload ID since parts are associated with a single upload.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and the underlying REST API, go to
        `Working with Archives in Amazon Glacier`_ and `List Multipart
        Uploads `_ in the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type limit: string
        :param limit: Specifies the maximum number of uploads returned in the
            response body. If this value is not specified, the List Uploads
            operation returns up to 1,000 uploads.

        :type marker: string
        :param marker: An opaque string used for pagination. This value
            specifies the upload at which the listing of uploads should begin.
            Get the marker value from a previous List Uploads response. You
            need only include the marker if you are continuing the pagination
            of results started in a previous List Uploads request.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        uri = 'vaults/%s/multipart-uploads' % vault_name
        return self.make_request('GET', uri, params=params)

    def list_parts(self, vault_name, upload_id, limit=None, marker=None):
        """
        This operation lists the parts of an archive that have been
        uploaded in a specific multipart upload. You can make this
        request at any time during an in-progress multipart upload
        before you complete the upload (see CompleteMultipartUpload.
        List Parts returns an error for completed uploads. The list
        returned in the List Parts response is sorted by part range.

        The List Parts operation supports pagination. By default, this
        operation returns up to 1,000 uploaded parts in the response.
        You should always check the response for a `marker` at which
        to continue the list; if there are no more items the `marker`
        is `null`. To return a list of parts that begins at a specific
        part, set the `marker` request parameter to the value you
        obtained from a previous List Parts request. You can also
        limit the number of parts returned in the response by
        specifying the `limit` parameter in the request.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and the underlying REST API, go to
        `Working with Archives in Amazon Glacier`_ and `List Parts`_
        in the Amazon Glacier Developer Guide .

        :type vault_name: string
        :param vault_name: The name of the vault.

        :type upload_id: string
        :param upload_id: The upload ID of the multipart upload.

        :type marker: string
        :param marker: An opaque string used for pagination. This value
            specifies the part at which the listing of parts should begin. Get
            the marker value from the response of a previous List Parts
            response. You need only include the marker if you are continuing
            the pagination of results started in a previous List Parts request.

        :type limit: string
        :param limit: Specifies the maximum number of parts returned in the
            response body. If this value is not specified, the List Parts
            operation returns up to 1,000 uploads.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        return self.make_request('GET', uri, params=params)

    def upload_part(self, vault_name, upload_id, linear_hash,
                    tree_hash, byte_range, part_data):
        """
        This operation uploads a part of an archive. You can upload
        archive parts in any order. You can also upload them in
        parallel. You can upload up to 10,000 parts for a multipart
        upload.

        Amazon Glacier rejects your upload part request if any of the
        following conditions is true:


        + **SHA256 tree hash does not match**To ensure that part data
          is not corrupted in transmission, you compute a SHA256 tree
          hash of the part and include it in your request. Upon
          receiving the part data, Amazon Glacier also computes a SHA256
          tree hash. If these hash values don't match, the operation
          fails. For information about computing a SHA256 tree hash, see
          `Computing Checksums`_.
        + **Part size does not match**The size of each part except the
          last must match the size specified in the corresponding
          InitiateMultipartUpload request. The size of the last part
          must be the same size as, or smaller than, the specified size.
          If you upload a part whose size is smaller than the part size
          you specified in your initiate multipart upload request and
          that part is not the last part, then the upload part request
          will succeed. However, the subsequent Complete Multipart
          Upload request will fail.
        + **Range does not align**The byte range value in the request
          does not align with the part size specified in the
          corresponding initiate request. For example, if you specify a
          part size of 4194304 bytes (4 MB), then 0 to 4194303 bytes (4
          MB - 1) and 4194304 (4 MB) to 8388607 (8 MB - 1) are valid
          part ranges. However, if you set a range value of 2 MB to 6
          MB, the range does not align with the part size and the upload
          will fail.


        This operation is idempotent. If you upload the same part
        multiple times, the data included in the most recent request
        overwrites the previously uploaded data.

        An AWS account has full permission to perform all operations
        (actions). However, AWS Identity and Access Management (IAM)
        users don't have any permissions by default. You must grant
        them explicit permission to perform specific actions. For more
        information, see `Access Control Using AWS Identity and Access
        Management (IAM)`_.

        For conceptual information and underlying REST API, go to
        `Uploading Large Archives in Parts (Multipart Upload)`_ and
        `Upload Part `_ in the Amazon Glacier Developer Guide .

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type linear_hash: str
        :param linear_hash: The SHA256 checksum (a linear hash) of the
            payload.

        :type tree_hash: str
        :param tree_hash: The user-computed SHA256 tree hash of the
            payload.  For more information on computing the
            tree hash, see http://goo.gl/u7chF.

        :type upload_id: str
        :param upload_id: The unique ID associated with this upload
            operation.

        :type byte_range: tuple of ints
        :param byte_range: Identifies the range of bytes in the assembled
            archive that will be uploaded in this part. Amazon Glacier uses
            this information to assemble the archive in the proper sequence.
            The format of this header follows RFC 2616. An example header is
            Content-Range:bytes 0-4194303/*.

        :type part_data: bytes
        :param part_data: The data to be uploaded for the part
        """
        headers = {'x-amz-content-sha256': linear_hash,
                   'x-amz-sha256-tree-hash': tree_hash,
                   'Content-Range': 'bytes %d-%d/*' % byte_range}
        response_headers = [('x-amz-sha256-tree-hash', u'TreeHash')]
        uri = 'vaults/%s/multipart-uploads/%s' % (str(vault_name), upload_id)
        return self.make_request('PUT', uri, headers=headers,
                                 data=part_data, ok_responses=(204,),
                                 response_headers=response_headers)
