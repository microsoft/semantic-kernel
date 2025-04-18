// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBNoDataConformanceTests(CosmosMongoDBNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<CosmosMongoDBNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoDBTestStore.Instance;
    }
}
