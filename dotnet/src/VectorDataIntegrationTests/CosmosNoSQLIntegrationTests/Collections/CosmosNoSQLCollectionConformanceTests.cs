// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Collections;

public class CosmosNoSQLCollectionConformanceTests(CosmosNoSQLFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<CosmosNoSQLFixture>
{
}
