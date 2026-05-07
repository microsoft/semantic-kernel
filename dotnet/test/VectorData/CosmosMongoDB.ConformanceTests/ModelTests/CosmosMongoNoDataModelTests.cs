// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.ModelTests;

public class CosmosMongoNoDataModelTests(CosmosMongoNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<CosmosMongoNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
