// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoCollectionManagementTests(CosmosMongoFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<CosmosMongoFixture>
{
}
