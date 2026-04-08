// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqliteVec.ConformanceTests;

public class SqliteDistanceFunctionTests(SqliteDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<int>(fixture), IClassFixture<SqliteDistanceFunctionTests.Fixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);
    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);

    public new class Fixture() : DistanceFunctionTests<int>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
