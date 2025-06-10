// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests.VectorSearch;

public class SqlServerVectorSearchDistanceFunctionComplianceTests_Hnsw(SqlServerFixture fixture)
    : SqlServerVectorSearchDistanceFunctionComplianceTests(fixture)
{
    // Creating such a collection is not supported.
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;

    public override async Task CosineDistance()
    {
        NotSupportedException ex = await Assert.ThrowsAsync<NotSupportedException>(() => base.CosineDistance());
        Assert.Equal($"Index kind {this.IndexKind} is not supported.", ex.Message);
    }

    public override async Task EuclideanDistance()
    {
        NotSupportedException ex = await Assert.ThrowsAsync<NotSupportedException>(() => base.EuclideanDistance());
        Assert.Equal($"Index kind {this.IndexKind} is not supported.", ex.Message);
    }

    public override async Task NegativeDotProductSimilarity()
    {
        NotSupportedException ex = await Assert.ThrowsAsync<NotSupportedException>(() => base.NegativeDotProductSimilarity());
        Assert.Equal($"Index kind {this.IndexKind} is not supported.", ex.Message);
    }
}
