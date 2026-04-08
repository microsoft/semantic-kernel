// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerDistanceFunctionTests(SqlServerDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<int>(fixture), IClassFixture<SqlServerDistanceFunctionTests.Fixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);
    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public new class Fixture() : DistanceFunctionTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
