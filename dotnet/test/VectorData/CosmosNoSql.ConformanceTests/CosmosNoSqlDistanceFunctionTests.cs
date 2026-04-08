// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlDistanceFunctionTests(CosmosNoSqlDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<string>(fixture), IClassFixture<CosmosNoSqlDistanceFunctionTests.Fixture>
{
    public override Task CosineDistance() => Assert.ThrowsAsync<NotSupportedException>(base.CosineDistance);
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public new class Fixture() : DistanceFunctionTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
