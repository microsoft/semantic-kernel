// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using MongoDB.Bson;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.TypeTests;

public class CosmosMongoKeyTypeTests(CosmosMongoKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<CosmosMongoKeyTypeTests.Fixture>
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
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
