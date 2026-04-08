// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests.ModelTests;

public class MongoBasicModelTests(MongoBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<MongoBasicModelTests.Fixture>
{
    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
