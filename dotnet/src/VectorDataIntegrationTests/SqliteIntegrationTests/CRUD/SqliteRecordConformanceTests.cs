// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteRecordConformanceTests(SqliteSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture>
{
}
