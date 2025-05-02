// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteRecordConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteRecordConformanceTests_ulong(SqliteSimpleModelFixture<ulong> fixture)
    : RecordConformanceTests<ulong>(fixture), IClassFixture<SqliteSimpleModelFixture<ulong>>
{
}
