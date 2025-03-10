// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace PineconeIntegrationTests.VectorSearch;

public class PineconeVectorSearchDistanceFunctionComplianceTests(PineconeFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<string>(fixture), IClassFixture<PineconeFixture>
{
    public override Task CosineDistance()
        => Assert.ThrowsAsync<NotSupportedException>(base.CosineDistance);

    public override Task EuclideanDistance()
        => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);

    public override Task Hamming()
        => Assert.ThrowsAsync<NotSupportedException>(base.Hamming);

    public override Task ManhattanDistance()
        => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public override Task NegativeDotProductSimilarity()
        => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
}
