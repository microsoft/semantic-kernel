// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.ModelTests;

public class CosmosMongoBasicModelTests(CosmosMongoBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<CosmosMongoBasicModelTests.Fixture>
{
    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
