// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using MongoDB.Bson;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.TypeTests;

public class CosmosMongoKeyTypeTests(CosmosMongoKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<CosmosMongoKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task ObjectId() => this.Test<ObjectId>(new("652f8c3e8f9b2c1a4d3e6a7b"), new("b7a6e3d4a1c2b9f8e3c8f256"));

    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    [ConditionalFact]
    public virtual Task Int() => this.Test<int>(8, 9);

    [ConditionalFact]
    public virtual Task Long() => this.Test<long>(8L, 9L);

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
