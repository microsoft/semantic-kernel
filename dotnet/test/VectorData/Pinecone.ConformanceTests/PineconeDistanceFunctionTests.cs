// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Pinecone.ConformanceTests;

public class PineconeDistanceFunctionTests(PineconeDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<string>(fixture), IClassFixture<PineconeDistanceFunctionTests.Fixture>
{
    public override Task CosineDistance() => Assert.ThrowsAsync<NotSupportedException>(base.CosineDistance);
    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);

    protected override async Task Test(
        string distanceFunction,
        double expectedExactMatchScore,
        double expectedOppositeScore,
        double expectedOrthogonalScore,
        int[] resultOrder)
    {
        await base.Test(
            distanceFunction,
            expectedExactMatchScore,
            expectedOppositeScore,
            expectedOrthogonalScore,
            resultOrder);

        // The Pinecone emulator needs some extra time to spawn a new index service
        // that uses a different distance function.
        await Task.Delay(TimeSpan.FromSeconds(5));
    }

    public new class Fixture() : DistanceFunctionTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;
    }
}
