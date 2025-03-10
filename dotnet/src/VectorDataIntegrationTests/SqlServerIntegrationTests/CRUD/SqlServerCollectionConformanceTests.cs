// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerCollectionConformanceTests(SqlServerFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
