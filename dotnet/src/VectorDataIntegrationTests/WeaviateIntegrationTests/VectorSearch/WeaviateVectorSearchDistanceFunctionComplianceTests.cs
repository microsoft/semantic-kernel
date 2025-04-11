// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.VectorSearch;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.VectorSearch;

public class WeaviateVectorSearchDistanceFunctionComplianceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);

    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);

    /// <summary>
    /// Tests vector search using <see cref="DistanceFunction.NegativeDotProductSimilarity"/>, computing -(u · v) as a distance metric per Weaviate's convention.
    /// Expects scores of -1 (exact match), 1 (opposite), and 0 (orthogonal), sorted ascending ([0, 2, 1]), with lower scores indicating closer matches.
    /// <see href="https://weaviate.io/developers/weaviate/config-refs/distances#available-distance-metrics"/>.
    /// </summary>
    public override Task NegativeDotProductSimilarity() => this.SimpleSearch(DistanceFunction.NegativeDotProductSimilarity, -1, 1, 0, [0, 2, 1]);
}

public class WeaviateVectorSearchDistanceFunctionComplianceTests_UnnamedVector(WeaviateDynamicDataModelNamedVectorsFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelNamedVectorsFixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);

    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);

    /// <summary>
    /// Tests vector search using <see cref="DistanceFunction.NegativeDotProductSimilarity"/>, computing -(u · v) as a distance metric per Weaviate's convention.
    /// Expects scores of -1 (exact match), 1 (opposite), and 0 (orthogonal), sorted ascending ([0, 2, 1]), with lower scores indicating closer matches.
    /// <see href="https://weaviate.io/developers/weaviate/config-refs/distances#available-distance-metrics"/>.
    /// </summary>
    public override Task NegativeDotProductSimilarity() => this.SimpleSearch(DistanceFunction.NegativeDotProductSimilarity, -1, 1, 0, [0, 2, 1]);
}
