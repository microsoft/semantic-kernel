// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlCollectionManagementTests(CosmosNoSqlFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<CosmosNoSqlFixture>
{
}
