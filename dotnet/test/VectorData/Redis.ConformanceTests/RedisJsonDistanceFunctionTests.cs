// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;
using Xunit.Sdk;

namespace Redis.ConformanceTests;

public class RedisJsonDistanceFunctionTests(RedisJsonDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<string>(fixture), IClassFixture<RedisJsonDistanceFunctionTests.Fixture>
{
    // Excluding DotProductSimilarity from the test even though Redis supports it, because the values that redis returns
    // are neither DotProductSimilarity nor NegativeDotProduct, but rather 1 - DotProductSimilarity.
    public override Task DotProductSimilarity() => Assert.ThrowsAsync<EqualException>(base.DotProductSimilarity);

    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public new class Fixture() : DistanceFunctionTests<string>.Fixture
    {
        private int _collectionCounter;

        public override TestStore TestStore => RedisTestStore.JsonInstance;

        // Redis doesn't seem to reliably delete the collection: when running multiple tests that delete and recreate the collection with different key types,
        // we seem to get key values from the previous collection despite having deleted and recreated it. So we uniquify the collection name instead.
        public override string CollectionName => "DistanceFunctionTests" + (++this._collectionCounter);
    }
}
