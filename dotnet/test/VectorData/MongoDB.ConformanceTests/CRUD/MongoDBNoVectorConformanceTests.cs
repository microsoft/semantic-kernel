// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace MongoDBIntegrationTests.CRUD;

public class MongoDBNoVectorConformanceTests(MongoDBNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<MongoDBNoVectorConformanceTests.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => MongoDBTestStore.Instance;
    }
}
