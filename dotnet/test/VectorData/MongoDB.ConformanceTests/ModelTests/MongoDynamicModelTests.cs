// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests.ModelTests;

public class MongoDynamicModelTests(MongoDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<MongoDynamicModelTests.Fixture>
{
    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
