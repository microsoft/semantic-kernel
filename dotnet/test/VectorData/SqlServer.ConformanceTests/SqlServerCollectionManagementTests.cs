// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerCollectionManagementTests(SqlServerFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
