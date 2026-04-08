// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.ModelTests;

public class CosmosMongoMultiVectorModelTests(CosmosMongoMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<string>(fixture), IClassFixture<CosmosMongoMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
