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

    public override async Task CosineSimilarity()
    {
        await base.CosineSimilarity();
        await ArtificialDelayToWorkaroundEmulatorLimitations();
    }

    public override async Task DotProductSimilarity()
    {
        await base.DotProductSimilarity();
        await ArtificialDelayToWorkaroundEmulatorLimitations();
    }

    public override Task EuclideanDistance()
        => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);

    public override async Task EuclideanSquaredDistance()
    {
        await base.EuclideanSquaredDistance();
        await ArtificialDelayToWorkaroundEmulatorLimitations();
    }

    public override Task Hamming()
        => Assert.ThrowsAsync<NotSupportedException>(base.Hamming);

    public override Task ManhattanDistance()
        => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public override Task NegativeDotProductSimilarity()
        => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);

    // The Pinecone emulator needs some extra time to spawn a new index service
    // that uses a different distance function.
    private static Task ArtificialDelayToWorkaroundEmulatorLimitations()
        => Task.Delay(TimeSpan.FromSeconds(5));
}
