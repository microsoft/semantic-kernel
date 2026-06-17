// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests;

public class MongoIndexKindTests(MongoIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<MongoIndexKindTests.Fixture>
{
    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
