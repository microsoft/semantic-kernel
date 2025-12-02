// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoIndexKindTests(CosmosMongoIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<CosmosMongoIndexKindTests.Fixture>
{
    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
