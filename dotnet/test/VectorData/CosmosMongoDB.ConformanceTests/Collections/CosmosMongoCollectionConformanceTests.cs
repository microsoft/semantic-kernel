// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.Collections;

public class CosmosMongoCollectionConformanceTests(CosmosMongoFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<CosmosMongoFixture>
{
}
