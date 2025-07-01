// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace CosmosNoSql.ConformanceTests.Collections;

public class CosmosNoSqlCollectionConformanceTests(CosmosNoSqlFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<CosmosNoSqlFixture>
{
}
