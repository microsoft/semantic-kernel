// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.VectorSearch;
using Xunit;

namespace SqlServer.ConformanceTests.VectorSearch;

public class SqlServerVectorSearchDistanceFunctionComplianceTests(SqlServerFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<int>(fixture), IClassFixture<SqlServerFixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);

    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);

    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);

    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);
}
