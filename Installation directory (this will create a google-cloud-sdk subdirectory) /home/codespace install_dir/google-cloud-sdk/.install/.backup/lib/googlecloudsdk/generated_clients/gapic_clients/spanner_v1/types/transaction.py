# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from cloudsdk.google.protobuf import duration_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.spanner.v1',
    manifest={
        'TransactionOptions',
        'Transaction',
        'TransactionSelector',
    },
)


class TransactionOptions(proto.Message):
    r"""Transactions:

    Each session can have at most one active transaction at a time (note
    that standalone reads and queries use a transaction internally and
    do count towards the one transaction limit). After the active
    transaction is completed, the session can immediately be re-used for
    the next transaction. It is not necessary to create a new session
    for each transaction.

    Transaction modes:

    Cloud Spanner supports three transaction modes:

    1. Locking read-write. This type of transaction is the only way to
       write data into Cloud Spanner. These transactions rely on
       pessimistic locking and, if necessary, two-phase commit. Locking
       read-write transactions may abort, requiring the application to
       retry.

    2. Snapshot read-only. Snapshot read-only transactions provide
       guaranteed consistency across several reads, but do not allow
       writes. Snapshot read-only transactions can be configured to read
       at timestamps in the past, or configured to perform a strong read
       (where Spanner will select a timestamp such that the read is
       guaranteed to see the effects of all transactions that have
       committed before the start of the read). Snapshot read-only
       transactions do not need to be committed.

       Queries on change streams must be performed with the snapshot
       read-only transaction mode, specifying a strong read. Please see
       [TransactionOptions.ReadOnly.strong][google.spanner.v1.TransactionOptions.ReadOnly.strong]
       for more details.

    3. Partitioned DML. This type of transaction is used to execute a
       single Partitioned DML statement. Partitioned DML partitions the
       key space and runs the DML statement over each partition in
       parallel using separate, internal transactions that commit
       independently. Partitioned DML transactions do not need to be
       committed.

    For transactions that only read, snapshot read-only transactions
    provide simpler semantics and are almost always faster. In
    particular, read-only transactions do not take locks, so they do not
    conflict with read-write transactions. As a consequence of not
    taking locks, they also do not abort, so retry loops are not needed.

    Transactions may only read-write data in a single database. They
    may, however, read-write data in different tables within that
    database.

    Locking read-write transactions:

    Locking transactions may be used to atomically read-modify-write
    data anywhere in a database. This type of transaction is externally
    consistent.

    Clients should attempt to minimize the amount of time a transaction
    is active. Faster transactions commit with higher probability and
    cause less contention. Cloud Spanner attempts to keep read locks
    active as long as the transaction continues to do reads, and the
    transaction has not been terminated by
    [Commit][google.spanner.v1.Spanner.Commit] or
    [Rollback][google.spanner.v1.Spanner.Rollback]. Long periods of
    inactivity at the client may cause Cloud Spanner to release a
    transaction's locks and abort it.

    Conceptually, a read-write transaction consists of zero or more
    reads or SQL statements followed by
    [Commit][google.spanner.v1.Spanner.Commit]. At any time before
    [Commit][google.spanner.v1.Spanner.Commit], the client can send a
    [Rollback][google.spanner.v1.Spanner.Rollback] request to abort the
    transaction.

    Semantics:

    Cloud Spanner can commit the transaction if all read locks it
    acquired are still valid at commit time, and it is able to acquire
    write locks for all writes. Cloud Spanner can abort the transaction
    for any reason. If a commit attempt returns ``ABORTED``, Cloud
    Spanner guarantees that the transaction has not modified any user
    data in Cloud Spanner.

    Unless the transaction commits, Cloud Spanner makes no guarantees
    about how long the transaction's locks were held for. It is an error
    to use Cloud Spanner locks for any sort of mutual exclusion other
    than between Cloud Spanner transactions themselves.

    Retrying aborted transactions:

    When a transaction aborts, the application can choose to retry the
    whole transaction again. To maximize the chances of successfully
    committing the retry, the client should execute the retry in the
    same session as the original attempt. The original session's lock
    priority increases with each consecutive abort, meaning that each
    attempt has a slightly better chance of success than the previous.

    Under some circumstances (for example, many transactions attempting
    to modify the same row(s)), a transaction can abort many times in a
    short period before successfully committing. Thus, it is not a good
    idea to cap the number of retries a transaction can attempt;
    instead, it is better to limit the total amount of time spent
    retrying.

    Idle transactions:

    A transaction is considered idle if it has no outstanding reads or
    SQL queries and has not started a read or SQL query within the last
    10 seconds. Idle transactions can be aborted by Cloud Spanner so
    that they don't hold on to locks indefinitely. If an idle
    transaction is aborted, the commit will fail with error ``ABORTED``.

    If this behavior is undesirable, periodically executing a simple SQL
    query in the transaction (for example, ``SELECT 1``) prevents the
    transaction from becoming idle.

    Snapshot read-only transactions:

    Snapshot read-only transactions provides a simpler method than
    locking read-write transactions for doing several consistent reads.
    However, this type of transaction does not support writes.

    Snapshot transactions do not take locks. Instead, they work by
    choosing a Cloud Spanner timestamp, then executing all reads at that
    timestamp. Since they do not acquire locks, they do not block
    concurrent read-write transactions.

    Unlike locking read-write transactions, snapshot read-only
    transactions never abort. They can fail if the chosen read timestamp
    is garbage collected; however, the default garbage collection policy
    is generous enough that most applications do not need to worry about
    this in practice.

    Snapshot read-only transactions do not need to call
    [Commit][google.spanner.v1.Spanner.Commit] or
    [Rollback][google.spanner.v1.Spanner.Rollback] (and in fact are not
    permitted to do so).

    To execute a snapshot transaction, the client specifies a timestamp
    bound, which tells Cloud Spanner how to choose a read timestamp.

    The types of timestamp bound are:

    -  Strong (the default).
    -  Bounded staleness.
    -  Exact staleness.

    If the Cloud Spanner database to be read is geographically
    distributed, stale read-only transactions can execute more quickly
    than strong or read-write transactions, because they are able to
    execute far from the leader replica.

    Each type of timestamp bound is discussed in detail below.

    Strong: Strong reads are guaranteed to see the effects of all
    transactions that have committed before the start of the read.
    Furthermore, all rows yielded by a single read are consistent with
    each other -- if any part of the read observes a transaction, all
    parts of the read see the transaction.

    Strong reads are not repeatable: two consecutive strong read-only
    transactions might return inconsistent results if there are
    concurrent writes. If consistency across reads is required, the
    reads should be executed within a transaction or at an exact read
    timestamp.

    Queries on change streams (see below for more details) must also
    specify the strong read timestamp bound.

    See
    [TransactionOptions.ReadOnly.strong][google.spanner.v1.TransactionOptions.ReadOnly.strong].

    Exact staleness:

    These timestamp bounds execute reads at a user-specified timestamp.
    Reads at a timestamp are guaranteed to see a consistent prefix of
    the global transaction history: they observe modifications done by
    all transactions with a commit timestamp less than or equal to the
    read timestamp, and observe none of the modifications done by
    transactions with a larger commit timestamp. They will block until
    all conflicting transactions that may be assigned commit timestamps
    <= the read timestamp have finished.

    The timestamp can either be expressed as an absolute Cloud Spanner
    commit timestamp or a staleness relative to the current time.

    These modes do not require a "negotiation phase" to pick a
    timestamp. As a result, they execute slightly faster than the
    equivalent boundedly stale concurrency modes. On the other hand,
    boundedly stale reads usually return fresher results.

    See
    [TransactionOptions.ReadOnly.read_timestamp][google.spanner.v1.TransactionOptions.ReadOnly.read_timestamp]
    and
    [TransactionOptions.ReadOnly.exact_staleness][google.spanner.v1.TransactionOptions.ReadOnly.exact_staleness].

    Bounded staleness:

    Bounded staleness modes allow Cloud Spanner to pick the read
    timestamp, subject to a user-provided staleness bound. Cloud Spanner
    chooses the newest timestamp within the staleness bound that allows
    execution of the reads at the closest available replica without
    blocking.

    All rows yielded are consistent with each other -- if any part of
    the read observes a transaction, all parts of the read see the
    transaction. Boundedly stale reads are not repeatable: two stale
    reads, even if they use the same staleness bound, can execute at
    different timestamps and thus return inconsistent results.

    Boundedly stale reads execute in two phases: the first phase
    negotiates a timestamp among all replicas needed to serve the read.
    In the second phase, reads are executed at the negotiated timestamp.

    As a result of the two phase execution, bounded staleness reads are
    usually a little slower than comparable exact staleness reads.
    However, they are typically able to return fresher results, and are
    more likely to execute at the closest replica.

    Because the timestamp negotiation requires up-front knowledge of
    which rows will be read, it can only be used with single-use
    read-only transactions.

    See
    [TransactionOptions.ReadOnly.max_staleness][google.spanner.v1.TransactionOptions.ReadOnly.max_staleness]
    and
    [TransactionOptions.ReadOnly.min_read_timestamp][google.spanner.v1.TransactionOptions.ReadOnly.min_read_timestamp].

    Old read timestamps and garbage collection:

    Cloud Spanner continuously garbage collects deleted and overwritten
    data in the background to reclaim storage space. This process is
    known as "version GC". By default, version GC reclaims versions
    after they are one hour old. Because of this, Cloud Spanner cannot
    perform reads at read timestamps more than one hour in the past.
    This restriction also applies to in-progress reads and/or SQL
    queries whose timestamp become too old while executing. Reads and
    SQL queries with too-old read timestamps fail with the error
    ``FAILED_PRECONDITION``.

    You can configure and extend the ``VERSION_RETENTION_PERIOD`` of a
    database up to a period as long as one week, which allows Cloud
    Spanner to perform reads up to one week in the past.

    Querying change Streams:

    A Change Stream is a schema object that can be configured to watch
    data changes on the entire database, a set of tables, or a set of
    columns in a database.

    When a change stream is created, Spanner automatically defines a
    corresponding SQL Table-Valued Function (TVF) that can be used to
    query the change records in the associated change stream using the
    ExecuteStreamingSql API. The name of the TVF for a change stream is
    generated from the name of the change stream:
    READ_<change_stream_name>.

    All queries on change stream TVFs must be executed using the
    ExecuteStreamingSql API with a single-use read-only transaction with
    a strong read-only timestamp_bound. The change stream TVF allows
    users to specify the start_timestamp and end_timestamp for the time
    range of interest. All change records within the retention period is
    accessible using the strong read-only timestamp_bound. All other
    TransactionOptions are invalid for change stream queries.

    In addition, if TransactionOptions.read_only.return_read_timestamp
    is set to true, a special value of 2^63 - 2 will be returned in the
    [Transaction][google.spanner.v1.Transaction] message that describes
    the transaction, instead of a valid read timestamp. This special
    value should be discarded and not used for any subsequent queries.

    Please see https://cloud.google.com/spanner/docs/change-streams for
    more details on how to query the change stream TVFs.

    Partitioned DML transactions:

    Partitioned DML transactions are used to execute DML statements with
    a different execution strategy that provides different, and often
    better, scalability properties for large, table-wide operations than
    DML in a ReadWrite transaction. Smaller scoped statements, such as
    an OLTP workload, should prefer using ReadWrite transactions.

    Partitioned DML partitions the keyspace and runs the DML statement
    on each partition in separate, internal transactions. These
    transactions commit automatically when complete, and run
    independently from one another.

    To reduce lock contention, this execution strategy only acquires
    read locks on rows that match the WHERE clause of the statement.
    Additionally, the smaller per-partition transactions hold locks for
    less time.

    That said, Partitioned DML is not a drop-in replacement for standard
    DML used in ReadWrite transactions.

    -  The DML statement must be fully-partitionable. Specifically, the
       statement must be expressible as the union of many statements
       which each access only a single row of the table.

    -  The statement is not applied atomically to all rows of the table.
       Rather, the statement is applied atomically to partitions of the
       table, in independent transactions. Secondary index rows are
       updated atomically with the base table rows.

    -  Partitioned DML does not guarantee exactly-once execution
       semantics against a partition. The statement will be applied at
       least once to each partition. It is strongly recommended that the
       DML statement should be idempotent to avoid unexpected results.
       For instance, it is potentially dangerous to run a statement such
       as ``UPDATE table SET column = column + 1`` as it could be run
       multiple times against some rows.

    -  The partitions are committed automatically - there is no support
       for Commit or Rollback. If the call returns an error, or if the
       client issuing the ExecuteSql call dies, it is possible that some
       rows had the statement executed on them successfully. It is also
       possible that statement was never executed against other rows.

    -  Partitioned DML transactions may only contain the execution of a
       single DML statement via ExecuteSql or ExecuteStreamingSql.

    -  If any error is encountered during the execution of the
       partitioned DML operation (for instance, a UNIQUE INDEX
       violation, division by zero, or a value that cannot be stored due
       to schema constraints), then the operation is stopped at that
       point and an error is returned. It is possible that at this
       point, some partitions have been committed (or even committed
       multiple times), and other partitions have not been run at all.

    Given the above, Partitioned DML is good fit for large,
    database-wide, operations that are idempotent, such as deleting old
    rows from a very large table.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        read_write (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions.ReadWrite):
            Transaction may write.

            Authorization to begin a read-write transaction requires
            ``spanner.databases.beginOrRollbackReadWriteTransaction``
            permission on the ``session`` resource.

            This field is a member of `oneof`_ ``mode``.
        partitioned_dml (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions.PartitionedDml):
            Partitioned DML transaction.

            Authorization to begin a Partitioned DML transaction
            requires
            ``spanner.databases.beginPartitionedDmlTransaction``
            permission on the ``session`` resource.

            This field is a member of `oneof`_ ``mode``.
        read_only (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions.ReadOnly):
            Transaction will not write.

            Authorization to begin a read-only transaction requires
            ``spanner.databases.beginReadOnlyTransaction`` permission on
            the ``session`` resource.

            This field is a member of `oneof`_ ``mode``.
        exclude_txn_from_change_streams (bool):
            When ``exclude_txn_from_change_streams`` is set to ``true``:

            -  Mutations from this transaction will not be recorded in
               change streams with DDL option
               ``allow_txn_exclusion=true`` that are tracking columns
               modified by these transactions.
            -  Mutations from this transaction will be recorded in
               change streams with DDL option
               ``allow_txn_exclusion=false or not set`` that are
               tracking columns modified by these transactions.

            When ``exclude_txn_from_change_streams`` is set to ``false``
            or not set, mutations from this transaction will be recorded
            in all change streams that are tracking columns modified by
            these transactions. ``exclude_txn_from_change_streams`` may
            only be specified for read-write or partitioned-dml
            transactions, otherwise the API will return an
            ``INVALID_ARGUMENT`` error.
    """

    class ReadWrite(proto.Message):
        r"""Message type to initiate a read-write transaction. Currently
        this transaction type has no options.

        Attributes:
            read_lock_mode (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions.ReadWrite.ReadLockMode):
                Read lock mode for the transaction.
        """
        class ReadLockMode(proto.Enum):
            r"""``ReadLockMode`` is used to set the read lock mode for read-write
            transactions.

            Values:
                READ_LOCK_MODE_UNSPECIFIED (0):
                    Default value.

                    If the value is not specified, the pessimistic
                    read lock is used.
                PESSIMISTIC (1):
                    Pessimistic lock mode.

                    Read locks are acquired immediately on read.
                OPTIMISTIC (2):
                    Optimistic lock mode.

                    Locks for reads within the transaction are not
                    acquired on read. Instead the locks are acquired
                    on a commit to validate that read/queried data
                    has not changed since the transaction started.
            """
            READ_LOCK_MODE_UNSPECIFIED = 0
            PESSIMISTIC = 1
            OPTIMISTIC = 2

        read_lock_mode: 'TransactionOptions.ReadWrite.ReadLockMode' = proto.Field(
            proto.ENUM,
            number=1,
            enum='TransactionOptions.ReadWrite.ReadLockMode',
        )

    class PartitionedDml(proto.Message):
        r"""Message type to initiate a Partitioned DML transaction.
        """

    class ReadOnly(proto.Message):
        r"""Message type to initiate a read-only transaction.

        This message has `oneof`_ fields (mutually exclusive fields).
        For each oneof, at most one member field can be set at the same time.
        Setting any member of the oneof automatically clears all other
        members.

        .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

        Attributes:
            strong (bool):
                Read at a timestamp where all previously
                committed transactions are visible.

                This field is a member of `oneof`_ ``timestamp_bound``.
            min_read_timestamp (google.protobuf.timestamp_pb2.Timestamp):
                Executes all reads at a timestamp >= ``min_read_timestamp``.

                This is useful for requesting fresher data than some
                previous read, or data that is fresh enough to observe the
                effects of some previously committed transaction whose
                timestamp is known.

                Note that this option can only be used in single-use
                transactions.

                A timestamp in RFC3339 UTC "Zulu" format, accurate to
                nanoseconds. Example: ``"2014-10-02T15:01:23.045123456Z"``.

                This field is a member of `oneof`_ ``timestamp_bound``.
            max_staleness (google.protobuf.duration_pb2.Duration):
                Read data at a timestamp >= ``NOW - max_staleness`` seconds.
                Guarantees that all writes that have committed more than the
                specified number of seconds ago are visible. Because Cloud
                Spanner chooses the exact timestamp, this mode works even if
                the client's local clock is substantially skewed from Cloud
                Spanner commit timestamps.

                Useful for reading the freshest data available at a nearby
                replica, while bounding the possible staleness if the local
                replica has fallen behind.

                Note that this option can only be used in single-use
                transactions.

                This field is a member of `oneof`_ ``timestamp_bound``.
            read_timestamp (google.protobuf.timestamp_pb2.Timestamp):
                Executes all reads at the given timestamp. Unlike other
                modes, reads at a specific timestamp are repeatable; the
                same read at the same timestamp always returns the same
                data. If the timestamp is in the future, the read will block
                until the specified timestamp, modulo the read's deadline.

                Useful for large scale consistent reads such as mapreduces,
                or for coordinating many reads against a consistent snapshot
                of the data.

                A timestamp in RFC3339 UTC "Zulu" format, accurate to
                nanoseconds. Example: ``"2014-10-02T15:01:23.045123456Z"``.

                This field is a member of `oneof`_ ``timestamp_bound``.
            exact_staleness (google.protobuf.duration_pb2.Duration):
                Executes all reads at a timestamp that is
                ``exact_staleness`` old. The timestamp is chosen soon after
                the read is started.

                Guarantees that all writes that have committed more than the
                specified number of seconds ago are visible. Because Cloud
                Spanner chooses the exact timestamp, this mode works even if
                the client's local clock is substantially skewed from Cloud
                Spanner commit timestamps.

                Useful for reading at nearby replicas without the
                distributed timestamp negotiation overhead of
                ``max_staleness``.

                This field is a member of `oneof`_ ``timestamp_bound``.
            return_read_timestamp (bool):
                If true, the Cloud Spanner-selected read timestamp is
                included in the [Transaction][google.spanner.v1.Transaction]
                message that describes the transaction.
        """

        strong: bool = proto.Field(
            proto.BOOL,
            number=1,
            oneof='timestamp_bound',
        )
        min_read_timestamp: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=2,
            oneof='timestamp_bound',
            message=timestamp_pb2.Timestamp,
        )
        max_staleness: duration_pb2.Duration = proto.Field(
            proto.MESSAGE,
            number=3,
            oneof='timestamp_bound',
            message=duration_pb2.Duration,
        )
        read_timestamp: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=4,
            oneof='timestamp_bound',
            message=timestamp_pb2.Timestamp,
        )
        exact_staleness: duration_pb2.Duration = proto.Field(
            proto.MESSAGE,
            number=5,
            oneof='timestamp_bound',
            message=duration_pb2.Duration,
        )
        return_read_timestamp: bool = proto.Field(
            proto.BOOL,
            number=6,
        )

    read_write: ReadWrite = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof='mode',
        message=ReadWrite,
    )
    partitioned_dml: PartitionedDml = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof='mode',
        message=PartitionedDml,
    )
    read_only: ReadOnly = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='mode',
        message=ReadOnly,
    )
    exclude_txn_from_change_streams: bool = proto.Field(
        proto.BOOL,
        number=5,
    )


class Transaction(proto.Message):
    r"""A transaction.

    Attributes:
        id (bytes):
            ``id`` may be used to identify the transaction in subsequent
            [Read][google.spanner.v1.Spanner.Read],
            [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql],
            [Commit][google.spanner.v1.Spanner.Commit], or
            [Rollback][google.spanner.v1.Spanner.Rollback] calls.

            Single-use read-only transactions do not have IDs, because
            single-use transactions do not support multiple requests.
        read_timestamp (google.protobuf.timestamp_pb2.Timestamp):
            For snapshot read-only transactions, the read timestamp
            chosen for the transaction. Not returned by default: see
            [TransactionOptions.ReadOnly.return_read_timestamp][google.spanner.v1.TransactionOptions.ReadOnly.return_read_timestamp].

            A timestamp in RFC3339 UTC "Zulu" format, accurate to
            nanoseconds. Example: ``"2014-10-02T15:01:23.045123456Z"``.
    """

    id: bytes = proto.Field(
        proto.BYTES,
        number=1,
    )
    read_timestamp: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )


class TransactionSelector(proto.Message):
    r"""This message is used to select the transaction in which a
    [Read][google.spanner.v1.Spanner.Read] or
    [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql] call runs.

    See [TransactionOptions][google.spanner.v1.TransactionOptions] for
    more information about transactions.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        single_use (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions):
            Execute the read or SQL query in a temporary
            transaction. This is the most efficient way to
            execute a transaction that consists of a single
            SQL query.

            This field is a member of `oneof`_ ``selector``.
        id (bytes):
            Execute the read or SQL query in a
            previously-started transaction.

            This field is a member of `oneof`_ ``selector``.
        begin (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TransactionOptions):
            Begin a new transaction and execute this read or SQL query
            in it. The transaction ID of the new transaction is returned
            in
            [ResultSetMetadata.transaction][google.spanner.v1.ResultSetMetadata.transaction],
            which is a [Transaction][google.spanner.v1.Transaction].

            This field is a member of `oneof`_ ``selector``.
    """

    single_use: 'TransactionOptions' = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof='selector',
        message='TransactionOptions',
    )
    id: bytes = proto.Field(
        proto.BYTES,
        number=2,
        oneof='selector',
    )
    begin: 'TransactionOptions' = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof='selector',
        message='TransactionOptions',
    )


__all__ = tuple(sorted(__protobuf__.manifest))
