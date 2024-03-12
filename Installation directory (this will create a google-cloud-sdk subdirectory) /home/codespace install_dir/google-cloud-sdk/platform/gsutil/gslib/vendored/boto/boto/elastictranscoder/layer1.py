# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.compat import json
from boto.exception import JSONResponseError
from boto.connection import AWSAuthConnection
from boto.regioninfo import RegionInfo
from boto.elastictranscoder import exceptions


class ElasticTranscoderConnection(AWSAuthConnection):
    """
    AWS Elastic Transcoder Service
    The AWS Elastic Transcoder Service.
    """
    APIVersion = "2012-09-25"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "elastictranscoder.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "IncompatibleVersionException": exceptions.IncompatibleVersionException,
        "LimitExceededException": exceptions.LimitExceededException,
        "ResourceInUseException": exceptions.ResourceInUseException,
        "AccessDeniedException": exceptions.AccessDeniedException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InternalServiceException": exceptions.InternalServiceException,
        "ValidationException": exceptions.ValidationException,
    }


    def __init__(self, **kwargs):
        region = kwargs.get('region')
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        else:
            del kwargs['region']
        kwargs['host'] = region.endpoint
        super(ElasticTranscoderConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def cancel_job(self, id=None):
        """
        The CancelJob operation cancels an unfinished job.
        You can only cancel a job that has a status of `Submitted`. To
        prevent a pipeline from starting to process a job while you're
        getting the job identifier, use UpdatePipelineStatus to
        temporarily pause the pipeline.

        :type id: string
        :param id: The identifier of the job that you want to cancel.
        To get a list of the jobs (including their `jobId`) that have a status
            of `Submitted`, use the ListJobsByStatus API action.

        """
        uri = '/2012-09-25/jobs/{0}'.format(id)
        return self.make_request('DELETE', uri, expected_status=202)

    def create_job(self, pipeline_id=None, input_name=None, output=None,
                   outputs=None, output_key_prefix=None, playlists=None):
        """
        When you create a job, Elastic Transcoder returns JSON data
        that includes the values that you specified plus information
        about the job that is created.

        If you have specified more than one output for your jobs (for
        example, one output for the Kindle Fire and another output for
        the Apple iPhone 4s), you currently must use the Elastic
        Transcoder API to list the jobs (as opposed to the AWS
        Console).

        :type pipeline_id: string
        :param pipeline_id: The `Id` of the pipeline that you want Elastic
            Transcoder to use for transcoding. The pipeline determines several
            settings, including the Amazon S3 bucket from which Elastic
            Transcoder gets the files to transcode and the bucket into which
            Elastic Transcoder puts the transcoded files.

        :type input_name: dict
        :param input_name: A section of the request body that provides
            information about the file that is being transcoded.

        :type output: dict
        :param output: The `CreateJobOutput` structure.

        :type outputs: list
        :param outputs: A section of the request body that provides information
            about the transcoded (target) files. We recommend that you use the
            `Outputs` syntax instead of the `Output` syntax.

        :type output_key_prefix: string
        :param output_key_prefix: The value, if any, that you want Elastic
            Transcoder to prepend to the names of all files that this job
            creates, including output files, thumbnails, and playlists.

        :type playlists: list
        :param playlists: If you specify a preset in `PresetId` for which the
            value of `Container` is ts (MPEG-TS), Playlists contains
            information about the master playlists that you want Elastic
            Transcoder to create.
        We recommend that you create only one master playlist. The maximum
            number of master playlists in a job is 30.

        """
        uri = '/2012-09-25/jobs'
        params = {}
        if pipeline_id is not None:
            params['PipelineId'] = pipeline_id
        if input_name is not None:
            params['Input'] = input_name
        if output is not None:
            params['Output'] = output
        if outputs is not None:
            params['Outputs'] = outputs
        if output_key_prefix is not None:
            params['OutputKeyPrefix'] = output_key_prefix
        if playlists is not None:
            params['Playlists'] = playlists
        return self.make_request('POST', uri, expected_status=201,
                                 data=json.dumps(params))

    def create_pipeline(self, name=None, input_bucket=None,
                        output_bucket=None, role=None, notifications=None,
                        content_config=None, thumbnail_config=None):
        """
        The CreatePipeline operation creates a pipeline with settings
        that you specify.

        :type name: string
        :param name: The name of the pipeline. We recommend that the name be
            unique within the AWS account, but uniqueness is not enforced.
        Constraints: Maximum 40 characters.

        :type input_bucket: string
        :param input_bucket: The Amazon S3 bucket in which you saved the media
            files that you want to transcode.

        :type output_bucket: string
        :param output_bucket: The Amazon S3 bucket in which you want Elastic
            Transcoder to save the transcoded files. (Use this, or use
            ContentConfig:Bucket plus ThumbnailConfig:Bucket.)
        Specify this value when all of the following are true:

        + You want to save transcoded files, thumbnails (if any), and playlists
              (if any) together in one bucket.
        + You do not want to specify the users or groups who have access to the
              transcoded files, thumbnails, and playlists.
        + You do not want to specify the permissions that Elastic Transcoder
              grants to the files. When Elastic Transcoder saves files in
              `OutputBucket`, it grants full control over the files only to the
              AWS account that owns the role that is specified by `Role`.
        + You want to associate the transcoded files and thumbnails with the
              Amazon S3 Standard storage class.



        If you want to save transcoded files and playlists in one bucket and
            thumbnails in another bucket, specify which users can access the
            transcoded files or the permissions the users have, or change the
            Amazon S3 storage class, omit `OutputBucket` and specify values for
            `ContentConfig` and `ThumbnailConfig` instead.

        :type role: string
        :param role: The IAM Amazon Resource Name (ARN) for the role that you
            want Elastic Transcoder to use to create the pipeline.

        :type notifications: dict
        :param notifications:
        The Amazon Simple Notification Service (Amazon SNS) topic that you want
            to notify to report job status.
        To receive notifications, you must also subscribe to the new topic in
            the Amazon SNS console.

        + **Progressing**: The topic ARN for the Amazon Simple Notification
              Service (Amazon SNS) topic that you want to notify when Elastic
              Transcoder has started to process a job in this pipeline. This is
              the ARN that Amazon SNS returned when you created the topic. For
              more information, see Create a Topic in the Amazon Simple
              Notification Service Developer Guide.
        + **Completed**: The topic ARN for the Amazon SNS topic that you want
              to notify when Elastic Transcoder has finished processing a job in
              this pipeline. This is the ARN that Amazon SNS returned when you
              created the topic.
        + **Warning**: The topic ARN for the Amazon SNS topic that you want to
              notify when Elastic Transcoder encounters a warning condition while
              processing a job in this pipeline. This is the ARN that Amazon SNS
              returned when you created the topic.
        + **Error**: The topic ARN for the Amazon SNS topic that you want to
              notify when Elastic Transcoder encounters an error condition while
              processing a job in this pipeline. This is the ARN that Amazon SNS
              returned when you created the topic.

        :type content_config: dict
        :param content_config:
        The optional `ContentConfig` object specifies information about the
            Amazon S3 bucket in which you want Elastic Transcoder to save
            transcoded files and playlists: which bucket to use, which users
            you want to have access to the files, the type of access you want
            users to have, and the storage class that you want to assign to the
            files.

        If you specify values for `ContentConfig`, you must also specify values
            for `ThumbnailConfig`.

        If you specify values for `ContentConfig` and `ThumbnailConfig`, omit
            the `OutputBucket` object.


        + **Bucket**: The Amazon S3 bucket in which you want Elastic Transcoder
              to save transcoded files and playlists.
        + **Permissions** (Optional): The Permissions object specifies which
              users you want to have access to transcoded files and the type of
              access you want them to have. You can grant permissions to a
              maximum of 30 users and/or predefined Amazon S3 groups.
        + **Grantee Type**: Specify the type of value that appears in the
              `Grantee` object:

            + **Canonical**: The value in the `Grantee` object is either the
                  canonical user ID for an AWS account or an origin access identity
                  for an Amazon CloudFront distribution. For more information about
                  canonical user IDs, see Access Control List (ACL) Overview in the
                  Amazon Simple Storage Service Developer Guide. For more information
                  about using CloudFront origin access identities to require that
                  users use CloudFront URLs instead of Amazon S3 URLs, see Using an
                  Origin Access Identity to Restrict Access to Your Amazon S3
                  Content. A canonical user ID is not the same as an AWS account
                  number.
            + **Email**: The value in the `Grantee` object is the registered email
                  address of an AWS account.
            + **Group**: The value in the `Grantee` object is one of the following
                  predefined Amazon S3 groups: `AllUsers`, `AuthenticatedUsers`, or
                  `LogDelivery`.

        + **Grantee**: The AWS user or group that you want to have access to
              transcoded files and playlists. To identify the user or group, you
              can specify the canonical user ID for an AWS account, an origin
              access identity for a CloudFront distribution, the registered email
              address of an AWS account, or a predefined Amazon S3 group
        + **Access**: The permission that you want to give to the AWS user that
              you specified in `Grantee`. Permissions are granted on the files
              that Elastic Transcoder adds to the bucket, including playlists and
              video files. Valid values include:

            + `READ`: The grantee can read the objects and metadata for objects
                  that Elastic Transcoder adds to the Amazon S3 bucket.
            + `READ_ACP`: The grantee can read the object ACL for objects that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `WRITE_ACP`: The grantee can write the ACL for the objects that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `FULL_CONTROL`: The grantee has `READ`, `READ_ACP`, and `WRITE_ACP`
                  permissions for the objects that Elastic Transcoder adds to the
                  Amazon S3 bucket.

        + **StorageClass**: The Amazon S3 storage class, `Standard` or
              `ReducedRedundancy`, that you want Elastic Transcoder to assign to
              the video files and playlists that it stores in your Amazon S3
              bucket.

        :type thumbnail_config: dict
        :param thumbnail_config:
        The `ThumbnailConfig` object specifies several values, including the
            Amazon S3 bucket in which you want Elastic Transcoder to save
            thumbnail files, which users you want to have access to the files,
            the type of access you want users to have, and the storage class
            that you want to assign to the files.

        If you specify values for `ContentConfig`, you must also specify values
            for `ThumbnailConfig` even if you don't want to create thumbnails.

        If you specify values for `ContentConfig` and `ThumbnailConfig`, omit
            the `OutputBucket` object.


        + **Bucket**: The Amazon S3 bucket in which you want Elastic Transcoder
              to save thumbnail files.
        + **Permissions** (Optional): The `Permissions` object specifies which
              users and/or predefined Amazon S3 groups you want to have access to
              thumbnail files, and the type of access you want them to have. You
              can grant permissions to a maximum of 30 users and/or predefined
              Amazon S3 groups.
        + **GranteeType**: Specify the type of value that appears in the
              Grantee object:

            + **Canonical**: The value in the `Grantee` object is either the
                  canonical user ID for an AWS account or an origin access identity
                  for an Amazon CloudFront distribution. A canonical user ID is not
                  the same as an AWS account number.
            + **Email**: The value in the `Grantee` object is the registered email
                  address of an AWS account.
            + **Group**: The value in the `Grantee` object is one of the following
                  predefined Amazon S3 groups: `AllUsers`, `AuthenticatedUsers`, or
                  `LogDelivery`.

        + **Grantee**: The AWS user or group that you want to have access to
              thumbnail files. To identify the user or group, you can specify the
              canonical user ID for an AWS account, an origin access identity for
              a CloudFront distribution, the registered email address of an AWS
              account, or a predefined Amazon S3 group.
        + **Access**: The permission that you want to give to the AWS user that
              you specified in `Grantee`. Permissions are granted on the
              thumbnail files that Elastic Transcoder adds to the bucket. Valid
              values include:

            + `READ`: The grantee can read the thumbnails and metadata for objects
                  that Elastic Transcoder adds to the Amazon S3 bucket.
            + `READ_ACP`: The grantee can read the object ACL for thumbnails that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `WRITE_ACP`: The grantee can write the ACL for the thumbnails that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `FULL_CONTROL`: The grantee has `READ`, `READ_ACP`, and `WRITE_ACP`
                  permissions for the thumbnails that Elastic Transcoder adds to the
                  Amazon S3 bucket.

        + **StorageClass**: The Amazon S3 storage class, `Standard` or
              `ReducedRedundancy`, that you want Elastic Transcoder to assign to
              the thumbnails that it stores in your Amazon S3 bucket.

        """
        uri = '/2012-09-25/pipelines'
        params = {}
        if name is not None:
            params['Name'] = name
        if input_bucket is not None:
            params['InputBucket'] = input_bucket
        if output_bucket is not None:
            params['OutputBucket'] = output_bucket
        if role is not None:
            params['Role'] = role
        if notifications is not None:
            params['Notifications'] = notifications
        if content_config is not None:
            params['ContentConfig'] = content_config
        if thumbnail_config is not None:
            params['ThumbnailConfig'] = thumbnail_config
        return self.make_request('POST', uri, expected_status=201,
                                 data=json.dumps(params))

    def create_preset(self, name=None, description=None, container=None,
                      video=None, audio=None, thumbnails=None):
        """
        The CreatePreset operation creates a preset with settings that
        you specify.
        Elastic Transcoder checks the CreatePreset settings to ensure
        that they meet Elastic Transcoder requirements and to
        determine whether they comply with H.264 standards. If your
        settings are not valid for Elastic Transcoder, Elastic
        Transcoder returns an HTTP 400 response (
        `ValidationException`) and does not create the preset. If the
        settings are valid for Elastic Transcoder but aren't strictly
        compliant with the H.264 standard, Elastic Transcoder creates
        the preset and returns a warning message in the response. This
        helps you determine whether your settings comply with the
        H.264 standard while giving you greater flexibility with
        respect to the video that Elastic Transcoder produces.
        Elastic Transcoder uses the H.264 video-compression format.
        For more information, see the International Telecommunication
        Union publication Recommendation ITU-T H.264: Advanced video
        coding for generic audiovisual services .

        :type name: string
        :param name: The name of the preset. We recommend that the name be
            unique within the AWS account, but uniqueness is not enforced.

        :type description: string
        :param description: A description of the preset.

        :type container: string
        :param container: The container type for the output file. Valid values
            include `mp3`, `mp4`, `ogg`, `ts`, and `webm`.

        :type video: dict
        :param video: A section of the request body that specifies the video
            parameters.

        :type audio: dict
        :param audio: A section of the request body that specifies the audio
            parameters.

        :type thumbnails: dict
        :param thumbnails: A section of the request body that specifies the
            thumbnail parameters, if any.

        """
        uri = '/2012-09-25/presets'
        params = {}
        if name is not None:
            params['Name'] = name
        if description is not None:
            params['Description'] = description
        if container is not None:
            params['Container'] = container
        if video is not None:
            params['Video'] = video
        if audio is not None:
            params['Audio'] = audio
        if thumbnails is not None:
            params['Thumbnails'] = thumbnails
        return self.make_request('POST', uri, expected_status=201,
                                 data=json.dumps(params))

    def delete_pipeline(self, id=None):
        """
        The DeletePipeline operation removes a pipeline.

        You can only delete a pipeline that has never been used or
        that is not currently in use (doesn't contain any active
        jobs). If the pipeline is currently in use, `DeletePipeline`
        returns an error.

        :type id: string
        :param id: The identifier of the pipeline that you want to delete.

        """
        uri = '/2012-09-25/pipelines/{0}'.format(id)
        return self.make_request('DELETE', uri, expected_status=202)

    def delete_preset(self, id=None):
        """
        The DeletePreset operation removes a preset that you've added
        in an AWS region.

        You can't delete the default presets that are included with
        Elastic Transcoder.

        :type id: string
        :param id: The identifier of the preset for which you want to get
            detailed information.

        """
        uri = '/2012-09-25/presets/{0}'.format(id)
        return self.make_request('DELETE', uri, expected_status=202)

    def list_jobs_by_pipeline(self, pipeline_id=None, ascending=None,
                              page_token=None):
        """
        The ListJobsByPipeline operation gets a list of the jobs
        currently in a pipeline.

        Elastic Transcoder returns all of the jobs currently in the
        specified pipeline. The response body contains one element for
        each job that satisfies the search criteria.

        :type pipeline_id: string
        :param pipeline_id: The ID of the pipeline for which you want to get
            job information.

        :type ascending: string
        :param ascending: To list jobs in chronological order by the date and
            time that they were submitted, enter `True`. To list jobs in
            reverse chronological order, enter `False`.

        :type page_token: string
        :param page_token: When Elastic Transcoder returns more than one page
            of results, use `pageToken` in subsequent `GET` requests to get
            each successive page of results.

        """
        uri = '/2012-09-25/jobsByPipeline/{0}'.format(pipeline_id)
        params = {}
        if pipeline_id is not None:
            params['PipelineId'] = pipeline_id
        if ascending is not None:
            params['Ascending'] = ascending
        if page_token is not None:
            params['PageToken'] = page_token
        return self.make_request('GET', uri, expected_status=200,
                                 params=params)

    def list_jobs_by_status(self, status=None, ascending=None,
                            page_token=None):
        """
        The ListJobsByStatus operation gets a list of jobs that have a
        specified status. The response body contains one element for
        each job that satisfies the search criteria.

        :type status: string
        :param status: To get information about all of the jobs associated with
            the current AWS account that have a given status, specify the
            following status: `Submitted`, `Progressing`, `Complete`,
            `Canceled`, or `Error`.

        :type ascending: string
        :param ascending: To list jobs in chronological order by the date and
            time that they were submitted, enter `True`. To list jobs in
            reverse chronological order, enter `False`.

        :type page_token: string
        :param page_token: When Elastic Transcoder returns more than one page
            of results, use `pageToken` in subsequent `GET` requests to get
            each successive page of results.

        """
        uri = '/2012-09-25/jobsByStatus/{0}'.format(status)
        params = {}
        if status is not None:
            params['Status'] = status
        if ascending is not None:
            params['Ascending'] = ascending
        if page_token is not None:
            params['PageToken'] = page_token
        return self.make_request('GET', uri, expected_status=200,
                                 params=params)

    def list_pipelines(self, ascending=None, page_token=None):
        """
        The ListPipelines operation gets a list of the pipelines
        associated with the current AWS account.

        :type ascending: string
        :param ascending: To list pipelines in chronological order by the date
            and time that they were created, enter `True`. To list pipelines in
            reverse chronological order, enter `False`.

        :type page_token: string
        :param page_token: When Elastic Transcoder returns more than one page
            of results, use `pageToken` in subsequent `GET` requests to get
            each successive page of results.

        """
        uri = '/2012-09-25/pipelines'.format()
        params = {}
        if ascending is not None:
            params['Ascending'] = ascending
        if page_token is not None:
            params['PageToken'] = page_token
        return self.make_request('GET', uri, expected_status=200,
                                 params=params)

    def list_presets(self, ascending=None, page_token=None):
        """
        The ListPresets operation gets a list of the default presets
        included with Elastic Transcoder and the presets that you've
        added in an AWS region.

        :type ascending: string
        :param ascending: To list presets in chronological order by the date
            and time that they were created, enter `True`. To list presets in
            reverse chronological order, enter `False`.

        :type page_token: string
        :param page_token: When Elastic Transcoder returns more than one page
            of results, use `pageToken` in subsequent `GET` requests to get
            each successive page of results.

        """
        uri = '/2012-09-25/presets'.format()
        params = {}
        if ascending is not None:
            params['Ascending'] = ascending
        if page_token is not None:
            params['PageToken'] = page_token
        return self.make_request('GET', uri, expected_status=200,
                                 params=params)

    def read_job(self, id=None):
        """
        The ReadJob operation returns detailed information about a
        job.

        :type id: string
        :param id: The identifier of the job for which you want to get detailed
            information.

        """
        uri = '/2012-09-25/jobs/{0}'.format(id)
        return self.make_request('GET', uri, expected_status=200)

    def read_pipeline(self, id=None):
        """
        The ReadPipeline operation gets detailed information about a
        pipeline.

        :type id: string
        :param id: The identifier of the pipeline to read.

        """
        uri = '/2012-09-25/pipelines/{0}'.format(id)
        return self.make_request('GET', uri, expected_status=200)

    def read_preset(self, id=None):
        """
        The ReadPreset operation gets detailed information about a
        preset.

        :type id: string
        :param id: The identifier of the preset for which you want to get
            detailed information.

        """
        uri = '/2012-09-25/presets/{0}'.format(id)
        return self.make_request('GET', uri, expected_status=200)

    def test_role(self, role=None, input_bucket=None, output_bucket=None,
                  topics=None):
        """
        The TestRole operation tests the IAM role used to create the
        pipeline.

        The `TestRole` action lets you determine whether the IAM role
        you are using has sufficient permissions to let Elastic
        Transcoder perform tasks associated with the transcoding
        process. The action attempts to assume the specified IAM role,
        checks read access to the input and output buckets, and tries
        to send a test notification to Amazon SNS topics that you
        specify.

        :type role: string
        :param role: The IAM Amazon Resource Name (ARN) for the role that you
            want Elastic Transcoder to test.

        :type input_bucket: string
        :param input_bucket: The Amazon S3 bucket that contains media files to
            be transcoded. The action attempts to read from this bucket.

        :type output_bucket: string
        :param output_bucket: The Amazon S3 bucket that Elastic Transcoder will
            write transcoded media files to. The action attempts to read from
            this bucket.

        :type topics: list
        :param topics: The ARNs of one or more Amazon Simple Notification
            Service (Amazon SNS) topics that you want the action to send a test
            notification to.

        """
        uri = '/2012-09-25/roleTests'
        params = {}
        if role is not None:
            params['Role'] = role
        if input_bucket is not None:
            params['InputBucket'] = input_bucket
        if output_bucket is not None:
            params['OutputBucket'] = output_bucket
        if topics is not None:
            params['Topics'] = topics
        return self.make_request('POST', uri, expected_status=200,
                                 data=json.dumps(params))

    def update_pipeline(self, id, name=None, input_bucket=None, role=None,
                        notifications=None, content_config=None,
                        thumbnail_config=None):
        """
        Use the `UpdatePipeline` operation to update settings for a
        pipeline. When you change pipeline settings, your changes take
        effect immediately. Jobs that you have already submitted and
        that Elastic Transcoder has not started to process are
        affected in addition to jobs that you submit after you change
        settings.

        :type id: string
        :param id: The ID of the pipeline that you want to update.

        :type name: string
        :param name: The name of the pipeline. We recommend that the name be
            unique within the AWS account, but uniqueness is not enforced.
        Constraints: Maximum 40 characters

        :type input_bucket: string
        :param input_bucket: The Amazon S3 bucket in which you saved the media
            files that you want to transcode and the graphics that you want to
            use as watermarks.

        :type role: string
        :param role: The IAM Amazon Resource Name (ARN) for the role that you
            want Elastic Transcoder to use to transcode jobs for this pipeline.

        :type notifications: dict
        :param notifications:
        The Amazon Simple Notification Service (Amazon SNS) topic or topics to
            notify in order to report job status.
        To receive notifications, you must also subscribe to the new topic in
            the Amazon SNS console.

        :type content_config: dict
        :param content_config:
        The optional `ContentConfig` object specifies information about the
            Amazon S3 bucket in which you want Elastic Transcoder to save
            transcoded files and playlists: which bucket to use, which users
            you want to have access to the files, the type of access you want
            users to have, and the storage class that you want to assign to the
            files.

        If you specify values for `ContentConfig`, you must also specify values
            for `ThumbnailConfig`.

        If you specify values for `ContentConfig` and `ThumbnailConfig`, omit
            the `OutputBucket` object.


        + **Bucket**: The Amazon S3 bucket in which you want Elastic Transcoder
              to save transcoded files and playlists.
        + **Permissions** (Optional): The Permissions object specifies which
              users you want to have access to transcoded files and the type of
              access you want them to have. You can grant permissions to a
              maximum of 30 users and/or predefined Amazon S3 groups.
        + **Grantee Type**: Specify the type of value that appears in the
              `Grantee` object:

            + **Canonical**: The value in the `Grantee` object is either the
                  canonical user ID for an AWS account or an origin access identity
                  for an Amazon CloudFront distribution. For more information about
                  canonical user IDs, see Access Control List (ACL) Overview in the
                  Amazon Simple Storage Service Developer Guide. For more information
                  about using CloudFront origin access identities to require that
                  users use CloudFront URLs instead of Amazon S3 URLs, see Using an
                  Origin Access Identity to Restrict Access to Your Amazon S3
                  Content. A canonical user ID is not the same as an AWS account
                  number.
            + **Email**: The value in the `Grantee` object is the registered email
                  address of an AWS account.
            + **Group**: The value in the `Grantee` object is one of the following
                  predefined Amazon S3 groups: `AllUsers`, `AuthenticatedUsers`, or
                  `LogDelivery`.

        + **Grantee**: The AWS user or group that you want to have access to
              transcoded files and playlists. To identify the user or group, you
              can specify the canonical user ID for an AWS account, an origin
              access identity for a CloudFront distribution, the registered email
              address of an AWS account, or a predefined Amazon S3 group
        + **Access**: The permission that you want to give to the AWS user that
              you specified in `Grantee`. Permissions are granted on the files
              that Elastic Transcoder adds to the bucket, including playlists and
              video files. Valid values include:

            + `READ`: The grantee can read the objects and metadata for objects
                  that Elastic Transcoder adds to the Amazon S3 bucket.
            + `READ_ACP`: The grantee can read the object ACL for objects that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `WRITE_ACP`: The grantee can write the ACL for the objects that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `FULL_CONTROL`: The grantee has `READ`, `READ_ACP`, and `WRITE_ACP`
                  permissions for the objects that Elastic Transcoder adds to the
                  Amazon S3 bucket.

        + **StorageClass**: The Amazon S3 storage class, `Standard` or
              `ReducedRedundancy`, that you want Elastic Transcoder to assign to
              the video files and playlists that it stores in your Amazon S3
              bucket.

        :type thumbnail_config: dict
        :param thumbnail_config:
        The `ThumbnailConfig` object specifies several values, including the
            Amazon S3 bucket in which you want Elastic Transcoder to save
            thumbnail files, which users you want to have access to the files,
            the type of access you want users to have, and the storage class
            that you want to assign to the files.

        If you specify values for `ContentConfig`, you must also specify values
            for `ThumbnailConfig` even if you don't want to create thumbnails.

        If you specify values for `ContentConfig` and `ThumbnailConfig`, omit
            the `OutputBucket` object.


        + **Bucket**: The Amazon S3 bucket in which you want Elastic Transcoder
              to save thumbnail files.
        + **Permissions** (Optional): The `Permissions` object specifies which
              users and/or predefined Amazon S3 groups you want to have access to
              thumbnail files, and the type of access you want them to have. You
              can grant permissions to a maximum of 30 users and/or predefined
              Amazon S3 groups.
        + **GranteeType**: Specify the type of value that appears in the
              Grantee object:

            + **Canonical**: The value in the `Grantee` object is either the
                  canonical user ID for an AWS account or an origin access identity
                  for an Amazon CloudFront distribution. A canonical user ID is not
                  the same as an AWS account number.
            + **Email**: The value in the `Grantee` object is the registered email
                  address of an AWS account.
            + **Group**: The value in the `Grantee` object is one of the following
                  predefined Amazon S3 groups: `AllUsers`, `AuthenticatedUsers`, or
                  `LogDelivery`.

        + **Grantee**: The AWS user or group that you want to have access to
              thumbnail files. To identify the user or group, you can specify the
              canonical user ID for an AWS account, an origin access identity for
              a CloudFront distribution, the registered email address of an AWS
              account, or a predefined Amazon S3 group.
        + **Access**: The permission that you want to give to the AWS user that
              you specified in `Grantee`. Permissions are granted on the
              thumbnail files that Elastic Transcoder adds to the bucket. Valid
              values include:

            + `READ`: The grantee can read the thumbnails and metadata for objects
                  that Elastic Transcoder adds to the Amazon S3 bucket.
            + `READ_ACP`: The grantee can read the object ACL for thumbnails that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `WRITE_ACP`: The grantee can write the ACL for the thumbnails that
                  Elastic Transcoder adds to the Amazon S3 bucket.
            + `FULL_CONTROL`: The grantee has `READ`, `READ_ACP`, and `WRITE_ACP`
                  permissions for the thumbnails that Elastic Transcoder adds to the
                  Amazon S3 bucket.

        + **StorageClass**: The Amazon S3 storage class, `Standard` or
              `ReducedRedundancy`, that you want Elastic Transcoder to assign to
              the thumbnails that it stores in your Amazon S3 bucket.

        """
        uri = '/2012-09-25/pipelines/{0}'.format(id)
        params = {}
        if name is not None:
            params['Name'] = name
        if input_bucket is not None:
            params['InputBucket'] = input_bucket
        if role is not None:
            params['Role'] = role
        if notifications is not None:
            params['Notifications'] = notifications
        if content_config is not None:
            params['ContentConfig'] = content_config
        if thumbnail_config is not None:
            params['ThumbnailConfig'] = thumbnail_config
        return self.make_request('PUT', uri, expected_status=200,
                                 data=json.dumps(params))

    def update_pipeline_notifications(self, id=None, notifications=None):
        """
        With the UpdatePipelineNotifications operation, you can update
        Amazon Simple Notification Service (Amazon SNS) notifications
        for a pipeline.

        When you update notifications for a pipeline, Elastic
        Transcoder returns the values that you specified in the
        request.

        :type id: string
        :param id: The identifier of the pipeline for which you want to change
            notification settings.

        :type notifications: dict
        :param notifications:
        The topic ARN for the Amazon Simple Notification Service (Amazon SNS)
            topic that you want to notify to report job status.
        To receive notifications, you must also subscribe to the new topic in
            the Amazon SNS console.

        + **Progressing**: The topic ARN for the Amazon Simple Notification
              Service (Amazon SNS) topic that you want to notify when Elastic
              Transcoder has started to process jobs that are added to this
              pipeline. This is the ARN that Amazon SNS returned when you created
              the topic.
        + **Completed**: The topic ARN for the Amazon SNS topic that you want
              to notify when Elastic Transcoder has finished processing a job.
              This is the ARN that Amazon SNS returned when you created the
              topic.
        + **Warning**: The topic ARN for the Amazon SNS topic that you want to
              notify when Elastic Transcoder encounters a warning condition. This
              is the ARN that Amazon SNS returned when you created the topic.
        + **Error**: The topic ARN for the Amazon SNS topic that you want to
              notify when Elastic Transcoder encounters an error condition. This
              is the ARN that Amazon SNS returned when you created the topic.

        """
        uri = '/2012-09-25/pipelines/{0}/notifications'.format(id)
        params = {}
        if id is not None:
            params['Id'] = id
        if notifications is not None:
            params['Notifications'] = notifications
        return self.make_request('POST', uri, expected_status=200,
                                 data=json.dumps(params))

    def update_pipeline_status(self, id=None, status=None):
        """
        The UpdatePipelineStatus operation pauses or reactivates a
        pipeline, so that the pipeline stops or restarts the
        processing of jobs.

        Changing the pipeline status is useful if you want to cancel
        one or more jobs. You can't cancel jobs after Elastic
        Transcoder has started processing them; if you pause the
        pipeline to which you submitted the jobs, you have more time
        to get the job IDs for the jobs that you want to cancel, and
        to send a CancelJob request.

        :type id: string
        :param id: The identifier of the pipeline to update.

        :type status: string
        :param status:
        The desired status of the pipeline:


        + `Active`: The pipeline is processing jobs.
        + `Paused`: The pipeline is not currently processing jobs.

        """
        uri = '/2012-09-25/pipelines/{0}/status'.format(id)
        params = {}
        if id is not None:
            params['Id'] = id
        if status is not None:
            params['Status'] = status
        return self.make_request('POST', uri, expected_status=200,
                                 data=json.dumps(params))

    def make_request(self, verb, resource, headers=None, data='',
                     expected_status=None, params=None):
        if headers is None:
            headers = {}
        response = super(ElasticTranscoderConnection, self).make_request(
            verb, resource, headers=headers, data=data, params=params)
        body = json.loads(response.read().decode('utf-8'))
        if response.status == expected_status:
            return body
        else:
            error_type = response.getheader('x-amzn-ErrorType').split(':')[0]
            error_class = self._faults.get(error_type, self.ResponseError)
            raise error_class(response.status, response.reason, body)
