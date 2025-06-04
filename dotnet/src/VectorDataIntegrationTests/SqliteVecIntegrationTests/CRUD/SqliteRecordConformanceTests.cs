// Copyright (c) Microsoft. All rights reserved.

using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteVecIntegrationTests.CRUD;

public class SqliteRecordConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteRecordConformanceTests_long(SqliteSimpleModelFixture<long> fixture)
    : RecordConformanceTests<long>(fixture), IClassFixture<SqliteSimpleModelFixture<long>>
{
}
