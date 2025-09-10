// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.VectorSearch;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.VectorSearch;

public class WeaviateVectorSearchDistanceFunctionComplianceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);

    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);
}

public class WeaviateVectorSearchDistanceFunctionComplianceTests_UnnamedVector(WeaviateDynamicDataModelNamedVectorsFixture fixture)
    : VectorSearchDistanceFunctionComplianceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelNamedVectorsFixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);

    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);
}
