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

import base64
import boto

from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.kinesis import exceptions
from boto.compat import json
from boto.compat import six


class KinesisConnection(AWSQueryConnection):
    """
    Amazon Kinesis Service API Reference
    Amazon Kinesis is a managed service that scales elastically for
    real time processing of streaming big data.
    """
    APIVersion = "2013-12-02"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "kinesis.us-east-1.amazonaws.com"
    ServiceName = "Kinesis"
    TargetPrefix = "Kinesis_20131202"
    ResponseError = JSONResponseError

    _faults = {
        "ProvisionedThroughputExceededException": exceptions.ProvisionedThroughputExceededException,
        "LimitExceededException": exceptions.LimitExceededException,
        "ExpiredIteratorException": exceptions.ExpiredIteratorException,
        "ResourceInUseException": exceptions.ResourceInUseException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InvalidArgumentException": exceptions.InvalidArgumentException,
        "SubscriptionRequiredException": exceptions.SubscriptionRequiredException
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint
        super(KinesisConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_tags_to_stream(self, stream_name, tags):
        """
        Adds or updates tags for the specified Amazon Kinesis stream.
        Each stream can have up to 10 tags.

        If tags have already been assigned to the stream,
        `AddTagsToStream` overwrites any existing tags that correspond
        to the specified tag keys.

        :type stream_name: string
        :param stream_name: The name of the stream.

        :type tags: map
        :param tags: The set of key-value pairs to use to create the tags.

        """
        params = {'StreamName': stream_name, 'Tags': tags, }
        return self.make_request(action='AddTagsToStream',
                                 body=json.dumps(params))

    def create_stream(self, stream_name, shard_count):
        """
        Creates a Amazon Kinesis stream. A stream captures and
        transports data records that are continuously emitted from
        different data sources or producers . Scale-out within an
        Amazon Kinesis stream is explicitly supported by means of
        shards, which are uniquely identified groups of data records
        in an Amazon Kinesis stream.

        You specify and control the number of shards that a stream is
        composed of. Each open shard can support up to 5 read
        transactions per second, up to a maximum total of 2 MB of data
        read per second. Each shard can support up to 1000 records
        written per second, up to a maximum total of 1 MB data written
        per second. You can add shards to a stream if the amount of
        data input increases and you can remove shards if the amount
        of data input decreases.

        The stream name identifies the stream. The name is scoped to
        the AWS account used by the application. It is also scoped by
        region. That is, two streams in two different accounts can
        have the same name, and two streams in the same account, but
        in two different regions, can have the same name.

        `CreateStream` is an asynchronous operation. Upon receiving a
        `CreateStream` request, Amazon Kinesis immediately returns and
        sets the stream status to `CREATING`. After the stream is
        created, Amazon Kinesis sets the stream status to `ACTIVE`.
        You should perform read and write operations only on an
        `ACTIVE` stream.

        You receive a `LimitExceededException` when making a
        `CreateStream` request if you try to do one of the following:


        + Have more than five streams in the `CREATING` state at any
          point in time.
        + Create more shards than are authorized for your account.


        The default limit for an AWS account is 10 shards per stream.
        If you need to create a stream with more than 10 shards,
        `contact AWS Support`_ to increase the limit on your account.

        You can use `DescribeStream` to check the stream status, which
        is returned in `StreamStatus`.

        `CreateStream` has a limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: A name to identify the stream. The stream name is
            scoped to the AWS account used by the application that creates the
            stream. It is also scoped by region. That is, two streams in two
            different AWS accounts can have the same name, and two streams in
            the same AWS account, but in two different regions, can have the
            same name.

        :type shard_count: integer
        :param shard_count: The number of shards that the stream will use. The
            throughput of the stream is a function of the number of shards;
            more shards are required for greater provisioned throughput.
        **Note:** The default limit for an AWS account is 10 shards per stream.
            If you need to create a stream with more than 10 shards, `contact
            AWS Support`_ to increase the limit on your account.

        """
        params = {
            'StreamName': stream_name,
            'ShardCount': shard_count,
        }
        return self.make_request(action='CreateStream',
                                 body=json.dumps(params))

    def delete_stream(self, stream_name):
        """
        Deletes a stream and all its shards and data. You must shut
        down any applications that are operating on the stream before
        you delete the stream. If an application attempts to operate
        on a deleted stream, it will receive the exception
        `ResourceNotFoundException`.

        If the stream is in the `ACTIVE` state, you can delete it.
        After a `DeleteStream` request, the specified stream is in the
        `DELETING` state until Amazon Kinesis completes the deletion.

        **Note:** Amazon Kinesis might continue to accept data read
        and write operations, such as PutRecord, PutRecords, and
        GetRecords, on a stream in the `DELETING` state until the
        stream deletion is complete.

        When you delete a stream, any shards in that stream are also
        deleted, and any tags are dissociated from the stream.

        You can use the DescribeStream operation to check the state of
        the stream, which is returned in `StreamStatus`.

        `DeleteStream` has a limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream to delete.

        """
        params = {'StreamName': stream_name, }
        return self.make_request(action='DeleteStream',
                                 body=json.dumps(params))

    def describe_stream(self, stream_name, limit=None,
                        exclusive_start_shard_id=None):
        """
        Describes the specified stream.

        The information about the stream includes its current status,
        its Amazon Resource Name (ARN), and an array of shard objects.
        For each shard object, there is information about the hash key
        and sequence number ranges that the shard spans, and the IDs
        of any earlier shards that played in a role in creating the
        shard. A sequence number is the identifier associated with
        every record ingested in the Amazon Kinesis stream. The
        sequence number is assigned when a record is put into the
        stream.

        You can limit the number of returned shards using the `Limit`
        parameter. The number of shards in a stream may be too large
        to return from a single call to `DescribeStream`. You can
        detect this by using the `HasMoreShards` flag in the returned
        output. `HasMoreShards` is set to `True` when there is more
        data available.

        `DescribeStream` is a paginated operation. If there are more
        shards available, you can request them using the shard ID of
        the last shard returned. Specify this ID in the
        `ExclusiveStartShardId` parameter in a subsequent request to
        `DescribeStream`.

        `DescribeStream` has a limit of 10 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream to describe.

        :type limit: integer
        :param limit: The maximum number of shards to return.

        :type exclusive_start_shard_id: string
        :param exclusive_start_shard_id: The shard ID of the shard to start
            with.

        """
        params = {'StreamName': stream_name, }
        if limit is not None:
            params['Limit'] = limit
        if exclusive_start_shard_id is not None:
            params['ExclusiveStartShardId'] = exclusive_start_shard_id
        return self.make_request(action='DescribeStream',
                                 body=json.dumps(params))

    def get_records(self, shard_iterator, limit=None, b64_decode=True):
        """
        Gets data records from a shard.

        Specify a shard iterator using the `ShardIterator` parameter.
        The shard iterator specifies the position in the shard from
        which you want to start reading data records sequentially. If
        there are no records available in the portion of the shard
        that the iterator points to, `GetRecords` returns an empty
        list. Note that it might take multiple calls to get to a
        portion of the shard that contains records.

        You can scale by provisioning multiple shards. Your
        application should have one thread per shard, each reading
        continuously from its stream. To read from a stream
        continually, call `GetRecords` in a loop. Use GetShardIterator
        to get the shard iterator to specify in the first `GetRecords`
        call. `GetRecords` returns a new shard iterator in
        `NextShardIterator`. Specify the shard iterator returned in
        `NextShardIterator` in subsequent calls to `GetRecords`. Note
        that if the shard has been closed, the shard iterator can't
        return more data and `GetRecords` returns `null` in
        `NextShardIterator`. You can terminate the loop when the shard
        is closed, or when the shard iterator reaches the record with
        the sequence number or other attribute that marks it as the
        last record to process.

        Each data record can be up to 50 KB in size, and each shard
        can read up to 2 MB per second. You can ensure that your calls
        don't exceed the maximum supported size or throughput by using
        the `Limit` parameter to specify the maximum number of records
        that `GetRecords` can return. Consider your average record
        size when determining this limit. For example, if your average
        record size is 40 KB, you can limit the data returned to about
        1 MB per call by specifying 25 as the limit.

        The size of the data returned by `GetRecords` will vary
        depending on the utilization of the shard. The maximum size of
        data that `GetRecords` can return is 10 MB. If a call returns
        10 MB of data, subsequent calls made within the next 5 seconds
        throw `ProvisionedThroughputExceededException`. If there is
        insufficient provisioned throughput on the shard, subsequent
        calls made within the next 1 second throw
        `ProvisionedThroughputExceededException`. Note that
        `GetRecords` won't return any data when it throws an
        exception. For this reason, we recommend that you wait one
        second between calls to `GetRecords`; however, it's possible
        that the application will get exceptions for longer than 1
        second.

        To detect whether the application is falling behind in
        processing, add a timestamp to your records and note how long
        it takes to process them. You can also monitor how much data
        is in a stream using the CloudWatch metrics for write
        operations ( `PutRecord` and `PutRecords`). For more
        information, see `Monitoring Amazon Kinesis with Amazon
        CloudWatch`_ in the Amazon Kinesis Developer Guide .

        :type shard_iterator: string
        :param shard_iterator: The position in the shard from which you want to
            start sequentially reading data records. A shard iterator specifies
            this position using the sequence number of a data record in the
            shard.

        :type limit: integer
        :param limit: The maximum number of records to return. Specify a value
            of up to 10,000. If you specify a value that is greater than
            10,000, `GetRecords` throws `InvalidArgumentException`.

        :type b64_decode: boolean
        :param b64_decode: Decode the Base64-encoded ``Data`` field of records.

        """
        params = {'ShardIterator': shard_iterator, }
        if limit is not None:
            params['Limit'] = limit

        response = self.make_request(action='GetRecords',
                                     body=json.dumps(params))

        # Base64 decode the data
        if b64_decode:
            for record in response.get('Records', []):
                record['Data'] = base64.b64decode(
                    record['Data'].encode('utf-8')).decode('utf-8')

        return response

    def get_shard_iterator(self, stream_name, shard_id, shard_iterator_type,
                           starting_sequence_number=None):
        """
        Gets a shard iterator. A shard iterator expires five minutes
        after it is returned to the requester.

        A shard iterator specifies the position in the shard from
        which to start reading data records sequentially. A shard
        iterator specifies this position using the sequence number of
        a data record in a shard. A sequence number is the identifier
        associated with every record ingested in the Amazon Kinesis
        stream. The sequence number is assigned when a record is put
        into the stream.

        You must specify the shard iterator type. For example, you can
        set the `ShardIteratorType` parameter to read exactly from the
        position denoted by a specific sequence number by using the
        `AT_SEQUENCE_NUMBER` shard iterator type, or right after the
        sequence number by using the `AFTER_SEQUENCE_NUMBER` shard
        iterator type, using sequence numbers returned by earlier
        calls to PutRecord, PutRecords, GetRecords, or DescribeStream.
        You can specify the shard iterator type `TRIM_HORIZON` in the
        request to cause `ShardIterator` to point to the last
        untrimmed record in the shard in the system, which is the
        oldest data record in the shard. Or you can point to just
        after the most recent record in the shard, by using the shard
        iterator type `LATEST`, so that you always read the most
        recent data in the shard.

        When you repeatedly read from an Amazon Kinesis stream use a
        GetShardIterator request to get the first shard iterator to to
        use in your first `GetRecords` request and then use the shard
        iterator returned by the `GetRecords` request in
        `NextShardIterator` for subsequent reads. A new shard iterator
        is returned by every `GetRecords` request in
        `NextShardIterator`, which you use in the `ShardIterator`
        parameter of the next `GetRecords` request.

        If a `GetShardIterator` request is made too often, you receive
        a `ProvisionedThroughputExceededException`. For more
        information about throughput limits, see GetRecords.

        If the shard is closed, the iterator can't return more data,
        and `GetShardIterator` returns `null` for its `ShardIterator`.
        A shard can be closed using SplitShard or MergeShards.

        `GetShardIterator` has a limit of 5 transactions per second
        per account per open shard.

        :type stream_name: string
        :param stream_name: The name of the stream.

        :type shard_id: string
        :param shard_id: The shard ID of the shard to get the iterator for.

        :type shard_iterator_type: string
        :param shard_iterator_type:
        Determines how the shard iterator is used to start reading data records
            from the shard.

        The following are the valid shard iterator types:


        + AT_SEQUENCE_NUMBER - Start reading exactly from the position denoted
              by a specific sequence number.
        + AFTER_SEQUENCE_NUMBER - Start reading right after the position
              denoted by a specific sequence number.
        + TRIM_HORIZON - Start reading at the last untrimmed record in the
              shard in the system, which is the oldest data record in the shard.
        + LATEST - Start reading just after the most recent record in the
              shard, so that you always read the most recent data in the shard.

        :type starting_sequence_number: string
        :param starting_sequence_number: The sequence number of the data record
            in the shard from which to start reading from.

        :returns: A dictionary containing:

            1) a `ShardIterator` with the value being the shard-iterator object
        """

        params = {
            'StreamName': stream_name,
            'ShardId': shard_id,
            'ShardIteratorType': shard_iterator_type,
        }
        if starting_sequence_number is not None:
            params['StartingSequenceNumber'] = starting_sequence_number
        return self.make_request(action='GetShardIterator',
                                 body=json.dumps(params))

    def list_streams(self, limit=None, exclusive_start_stream_name=None):
        """
        Lists your streams.

        The number of streams may be too large to return from a single
        call to `ListStreams`. You can limit the number of returned
        streams using the `Limit` parameter. If you do not specify a
        value for the `Limit` parameter, Amazon Kinesis uses the
        default limit, which is currently 10.

        You can detect if there are more streams available to list by
        using the `HasMoreStreams` flag from the returned output. If
        there are more streams available, you can request more streams
        by using the name of the last stream returned by the
        `ListStreams` request in the `ExclusiveStartStreamName`
        parameter in a subsequent request to `ListStreams`. The group
        of stream names returned by the subsequent request is then
        added to the list. You can continue this process until all the
        stream names have been collected in the list.

        `ListStreams` has a limit of 5 transactions per second per
        account.

        :type limit: integer
        :param limit: The maximum number of streams to list.

        :type exclusive_start_stream_name: string
        :param exclusive_start_stream_name: The name of the stream to start the
            list with.

        """
        params = {}
        if limit is not None:
            params['Limit'] = limit
        if exclusive_start_stream_name is not None:
            params['ExclusiveStartStreamName'] = exclusive_start_stream_name
        return self.make_request(action='ListStreams',
                                 body=json.dumps(params))

    def list_tags_for_stream(self, stream_name, exclusive_start_tag_key=None,
                             limit=None):
        """
        Lists the tags for the specified Amazon Kinesis stream.

        :type stream_name: string
        :param stream_name: The name of the stream.

        :type exclusive_start_tag_key: string
        :param exclusive_start_tag_key: The key to use as the starting point
            for the list of tags. If this parameter is set, `ListTagsForStream`
            gets all tags that occur after `ExclusiveStartTagKey`.

        :type limit: integer
        :param limit: The number of tags to return. If this number is less than
            the total number of tags associated with the stream, `HasMoreTags`
            is set to `True`. To list additional tags, set
            `ExclusiveStartTagKey` to the last key in the response.

        """
        params = {'StreamName': stream_name, }
        if exclusive_start_tag_key is not None:
            params['ExclusiveStartTagKey'] = exclusive_start_tag_key
        if limit is not None:
            params['Limit'] = limit
        return self.make_request(action='ListTagsForStream',
                                 body=json.dumps(params))

    def merge_shards(self, stream_name, shard_to_merge,
                     adjacent_shard_to_merge):
        """
        Merges two adjacent shards in a stream and combines them into
        a single shard to reduce the stream's capacity to ingest and
        transport data. Two shards are considered adjacent if the
        union of the hash key ranges for the two shards form a
        contiguous set with no gaps. For example, if you have two
        shards, one with a hash key range of 276...381 and the other
        with a hash key range of 382...454, then you could merge these
        two shards into a single shard that would have a hash key
        range of 276...454. After the merge, the single child shard
        receives data for all hash key values covered by the two
        parent shards.

        `MergeShards` is called when there is a need to reduce the
        overall capacity of a stream because of excess capacity that
        is not being used. You must specify the shard to be merged and
        the adjacent shard for a stream. For more information about
        merging shards, see `Merge Two Shards`_ in the Amazon Kinesis
        Developer Guide .

        If the stream is in the `ACTIVE` state, you can call
        `MergeShards`. If a stream is in the `CREATING`, `UPDATING`,
        or `DELETING` state, `MergeShards` returns a
        `ResourceInUseException`. If the specified stream does not
        exist, `MergeShards` returns a `ResourceNotFoundException`.

        You can use DescribeStream to check the state of the stream,
        which is returned in `StreamStatus`.

        `MergeShards` is an asynchronous operation. Upon receiving a
        `MergeShards` request, Amazon Kinesis immediately returns a
        response and sets the `StreamStatus` to `UPDATING`. After the
        operation is completed, Amazon Kinesis sets the `StreamStatus`
        to `ACTIVE`. Read and write operations continue to work while
        the stream is in the `UPDATING` state.

        You use DescribeStream to determine the shard IDs that are
        specified in the `MergeShards` request.

        If you try to operate on too many streams in parallel using
        CreateStream, DeleteStream, `MergeShards` or SplitShard, you
        will receive a `LimitExceededException`.

        `MergeShards` has limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream for the merge.

        :type shard_to_merge: string
        :param shard_to_merge: The shard ID of the shard to combine with the
            adjacent shard for the merge.

        :type adjacent_shard_to_merge: string
        :param adjacent_shard_to_merge: The shard ID of the adjacent shard for
            the merge.

        """
        params = {
            'StreamName': stream_name,
            'ShardToMerge': shard_to_merge,
            'AdjacentShardToMerge': adjacent_shard_to_merge,
        }
        return self.make_request(action='MergeShards',
                                 body=json.dumps(params))

    def put_record(self, stream_name, data, partition_key,
                   explicit_hash_key=None,
                   sequence_number_for_ordering=None,
                   exclusive_minimum_sequence_number=None,
                   b64_encode=True):
        """
        This operation puts a data record into an Amazon Kinesis
        stream from a producer. This operation must be called to send
        data from the producer into the Amazon Kinesis stream for
        real-time ingestion and subsequent processing. The `PutRecord`
        operation requires the name of the stream that captures,
        stores, and transports the data; a partition key; and the data
        blob itself. The data blob could be a segment from a log file,
        geographic/location data, website clickstream data, or any
        other data type.

        The partition key is used to distribute data across shards.
        Amazon Kinesis segregates the data records that belong to a
        data stream into multiple shards, using the partition key
        associated with each data record to determine which shard a
        given data record belongs to.

        Partition keys are Unicode strings, with a maximum length
        limit of 256 bytes. An MD5 hash function is used to map
        partition keys to 128-bit integer values and to map associated
        data records to shards using the hash key ranges of the
        shards. You can override hashing the partition key to
        determine the shard by explicitly specifying a hash value
        using the `ExplicitHashKey` parameter. For more information,
        see the `Amazon Kinesis Developer Guide`_.

        `PutRecord` returns the shard ID of where the data record was
        placed and the sequence number that was assigned to the data
        record.

        Sequence numbers generally increase over time. To guarantee
        strictly increasing ordering, use the
        `SequenceNumberForOrdering` parameter. For more information,
        see the `Amazon Kinesis Developer Guide`_.

        If a `PutRecord` request cannot be processed because of
        insufficient provisioned throughput on the shard involved in
        the request, `PutRecord` throws
        `ProvisionedThroughputExceededException`.

        Data records are accessible for only 24 hours from the time
        that they are added to an Amazon Kinesis stream.

        :type stream_name: string
        :param stream_name: The name of the stream to put the data record into.

        :type data: blob
        :param data: The data blob to put into the record, which is
            Base64-encoded when the blob is serialized.
            The maximum size of the data blob (the payload after
            Base64-decoding) is 50 kilobytes (KB)
            Set `b64_encode` to disable automatic Base64 encoding.

        :type partition_key: string
        :param partition_key: Determines which shard in the stream the data
            record is assigned to. Partition keys are Unicode strings with a
            maximum length limit of 256 bytes. Amazon Kinesis uses the
            partition key as input to a hash function that maps the partition
            key and associated data to a specific shard. Specifically, an MD5
            hash function is used to map partition keys to 128-bit integer
            values and to map associated data records to shards. As a result of
            this hashing mechanism, all data records with the same partition
            key will map to the same shard within the stream.

        :type explicit_hash_key: string
        :param explicit_hash_key: The hash value used to explicitly determine
            the shard the data record is assigned to by overriding the
            partition key hash.

        :type sequence_number_for_ordering: string
        :param sequence_number_for_ordering: Guarantees strictly increasing
            sequence numbers, for puts from the same client and to the same
            partition key. Usage: set the `SequenceNumberForOrdering` of record
            n to the sequence number of record n-1 (as returned in the
            PutRecordResult when putting record n-1 ). If this parameter is not
            set, records will be coarsely ordered based on arrival time.

        :type b64_encode: boolean
        :param b64_encode: Whether to Base64 encode `data`. Can be set to
            ``False`` if `data` is already encoded to prevent double encoding.

        """
        params = {
            'StreamName': stream_name,
            'Data': data,
            'PartitionKey': partition_key,
        }
        if explicit_hash_key is not None:
            params['ExplicitHashKey'] = explicit_hash_key
        if sequence_number_for_ordering is not None:
            params['SequenceNumberForOrdering'] = sequence_number_for_ordering
        if b64_encode:
            if not isinstance(params['Data'], six.binary_type):
                params['Data'] = params['Data'].encode('utf-8')
            params['Data'] = base64.b64encode(params['Data']).decode('utf-8')
        return self.make_request(action='PutRecord',
                                 body=json.dumps(params))

    def put_records(self, records, stream_name, b64_encode=True):
        """
        Puts (writes) multiple data records from a producer into an
        Amazon Kinesis stream in a single call (also referred to as a
        `PutRecords` request). Use this operation to send data from a
        data producer into the Amazon Kinesis stream for real-time
        ingestion and processing. Each shard can support up to 1000
        records written per second, up to a maximum total of 1 MB data
        written per second.

        You must specify the name of the stream that captures, stores,
        and transports the data; and an array of request `Records`,
        with each record in the array requiring a partition key and
        data blob.

        The data blob can be any type of data; for example, a segment
        from a log file, geographic/location data, website clickstream
        data, and so on.

        The partition key is used by Amazon Kinesis as input to a hash
        function that maps the partition key and associated data to a
        specific shard. An MD5 hash function is used to map partition
        keys to 128-bit integer values and to map associated data
        records to shards. As a result of this hashing mechanism, all
        data records with the same partition key map to the same shard
        within the stream. For more information, see `Partition Key`_
        in the Amazon Kinesis Developer Guide .

        Each record in the `Records` array may include an optional
        parameter, `ExplicitHashKey`, which overrides the partition
        key to shard mapping. This parameter allows a data producer to
        determine explicitly the shard where the record is stored. For
        more information, see `Adding Multiple Records with
        PutRecords`_ in the Amazon Kinesis Developer Guide .

        The `PutRecords` response includes an array of response
        `Records`. Each record in the response array directly
        correlates with a record in the request array using natural
        ordering, from the top to the bottom of the request and
        response. The response `Records` array always includes the
        same number of records as the request array.

        The response `Records` array includes both successfully and
        unsuccessfully processed records. Amazon Kinesis attempts to
        process all records in each `PutRecords` request. A single
        record failure does not stop the processing of subsequent
        records.

        A successfully-processed record includes `ShardId` and
        `SequenceNumber` values. The `ShardId` parameter identifies
        the shard in the stream where the record is stored. The
        `SequenceNumber` parameter is an identifier assigned to the
        put record, unique to all records in the stream.

        An unsuccessfully-processed record includes `ErrorCode` and
        `ErrorMessage` values. `ErrorCode` reflects the type of error
        and can be one of the following values:
        `ProvisionedThroughputExceededException` or `InternalFailure`.
        `ErrorMessage` provides more detailed information about the
        `ProvisionedThroughputExceededException` exception including
        the account ID, stream name, and shard ID of the record that
        was throttled.

        Data records are accessible for only 24 hours from the time
        that they are added to an Amazon Kinesis stream.

        :type records: list
        :param records: The records associated with the request.

        :type stream_name: string
        :param stream_name: The stream name associated with the request.

        :type b64_encode: boolean
        :param b64_encode: Whether to Base64 encode `data`. Can be set to
            ``False`` if `data` is already encoded to prevent double encoding.

        """
        params = {'Records': records, 'StreamName': stream_name, }
        if b64_encode:
            for i in range(len(params['Records'])):
                data = params['Records'][i]['Data']
                if not isinstance(data, six.binary_type):
                    data = data.encode('utf-8')
                params['Records'][i]['Data'] = base64.b64encode(
                    data).decode('utf-8')
        return self.make_request(action='PutRecords',
                                 body=json.dumps(params))

    def remove_tags_from_stream(self, stream_name, tag_keys):
        """
        Deletes tags from the specified Amazon Kinesis stream.

        If you specify a tag that does not exist, it is ignored.

        :type stream_name: string
        :param stream_name: The name of the stream.

        :type tag_keys: list
        :param tag_keys: A list of tag keys. Each corresponding tag is removed
            from the stream.

        """
        params = {'StreamName': stream_name, 'TagKeys': tag_keys, }
        return self.make_request(action='RemoveTagsFromStream',
                                 body=json.dumps(params))

    def split_shard(self, stream_name, shard_to_split, new_starting_hash_key):
        """
        Splits a shard into two new shards in the stream, to increase
        the stream's capacity to ingest and transport data.
        `SplitShard` is called when there is a need to increase the
        overall capacity of stream because of an expected increase in
        the volume of data records being ingested.

        You can also use `SplitShard` when a shard appears to be
        approaching its maximum utilization, for example, when the set
        of producers sending data into the specific shard are suddenly
        sending more than previously anticipated. You can also call
        `SplitShard` to increase stream capacity, so that more Amazon
        Kinesis applications can simultaneously read data from the
        stream for real-time processing.

        You must specify the shard to be split and the new hash key,
        which is the position in the shard where the shard gets split
        in two. In many cases, the new hash key might simply be the
        average of the beginning and ending hash key, but it can be
        any hash key value in the range being mapped into the shard.
        For more information about splitting shards, see `Split a
        Shard`_ in the Amazon Kinesis Developer Guide .

        You can use DescribeStream to determine the shard ID and hash
        key values for the `ShardToSplit` and `NewStartingHashKey`
        parameters that are specified in the `SplitShard` request.

        `SplitShard` is an asynchronous operation. Upon receiving a
        `SplitShard` request, Amazon Kinesis immediately returns a
        response and sets the stream status to `UPDATING`. After the
        operation is completed, Amazon Kinesis sets the stream status
        to `ACTIVE`. Read and write operations continue to work while
        the stream is in the `UPDATING` state.

        You can use `DescribeStream` to check the status of the
        stream, which is returned in `StreamStatus`. If the stream is
        in the `ACTIVE` state, you can call `SplitShard`. If a stream
        is in `CREATING` or `UPDATING` or `DELETING` states,
        `DescribeStream` returns a `ResourceInUseException`.

        If the specified stream does not exist, `DescribeStream`
        returns a `ResourceNotFoundException`. If you try to create
        more shards than are authorized for your account, you receive
        a `LimitExceededException`.

        The default limit for an AWS account is 10 shards per stream.
        If you need to create a stream with more than 10 shards,
        `contact AWS Support`_ to increase the limit on your account.

        If you try to operate on too many streams in parallel using
        CreateStream, DeleteStream, MergeShards or SplitShard, you
        receive a `LimitExceededException`.

        `SplitShard` has limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream for the shard split.

        :type shard_to_split: string
        :param shard_to_split: The shard ID of the shard to split.

        :type new_starting_hash_key: string
        :param new_starting_hash_key: A hash key value for the starting hash
            key of one of the child shards created by the split. The hash key
            range for a given shard constitutes a set of ordered contiguous
            positive integers. The value for `NewStartingHashKey` must be in
            the range of hash keys being mapped into the shard. The
            `NewStartingHashKey` hash key value and all higher hash key values
            in hash key range are distributed to one of the child shards. All
            the lower hash key values in the range are distributed to the other
            child shard.

        """
        params = {
            'StreamName': stream_name,
            'ShardToSplit': shard_to_split,
            'NewStartingHashKey': new_starting_hash_key,
        }
        return self.make_request(action='SplitShard',
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
        boto.log.debug(response.getheaders())
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

