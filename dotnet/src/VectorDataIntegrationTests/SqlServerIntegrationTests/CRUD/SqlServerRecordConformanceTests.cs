// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerRecordConformanceTests(SqlServerFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
