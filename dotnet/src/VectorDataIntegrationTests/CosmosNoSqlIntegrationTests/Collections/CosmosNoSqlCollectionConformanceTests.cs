// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace CosmosNoSqlIntegrationTests.Collections;

public class CosmosNoSqlCollectionConformanceTests(CosmosNoSqlFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<CosmosNoSqlFixture>
{
}
