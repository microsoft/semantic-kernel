// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoIndexKindTests(CosmosMongoIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<CosmosMongoIndexKindTests.Fixture>
{
    // Note: Cosmos Mongo support HNSW, but only in a specific tier.
    // [ConditionalFact]
    // public virtual Task Hnsw()
    //     => this.Test(IndexKind.Hnsw);

    [ConditionalFact]
    public virtual Task IvfFlat()
        => this.Test(IndexKind.IvfFlat);

    // Cosmos Mongo does not support index-less searching
    public override Task Flat() => Assert.ThrowsAsync<NotSupportedException>(base.Flat);

    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;
    }
}
