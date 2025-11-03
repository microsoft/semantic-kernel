// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchDistanceFunctionTests(AzureAISearchDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<string>(fixture), IClassFixture<AzureAISearchDistanceFunctionTests.Fixture>
{
    public override Task CosineDistance() => Assert.ThrowsAsync<NotSupportedException>(base.CosineDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public new class Fixture() : DistanceFunctionTests<string>.Fixture
    {
        public override string CollectionName => "distance-functions-" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // AzureAISearch does not return the expected standard mathematical result for each distance function
        public override bool AssertScores => false;
    }
}
