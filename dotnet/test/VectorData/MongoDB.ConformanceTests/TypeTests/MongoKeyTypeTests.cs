// Copyright (c) Microsoft. All rights reserved.

using MongoDB.Bson;
using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace MongoDB.ConformanceTests.TypeTests;

public class MongoKeyTypeTests(MongoKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<MongoKeyTypeTests.Fixture>
{
    [Fact]
    public virtual Task ObjectId() => this.Test<ObjectId>(new("652f8c3e8f9b2c1a4d3e6a7b"), supportsAutoGeneration: true);

    [Fact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    [Fact]
    public virtual Task Int() => this.Test<int>(8);

    [Fact]
    public virtual Task Long() => this.Test<long>(8L);

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
