// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.HybridSearch;

public class WeaviateKeywordVectorizedHybridSearchTests_UnnamedVectors(
    WeaviateKeywordVectorizedHybridSearchTests_UnnamedVectors.VectorAndStringFixture vectorAndStringFixture,
    WeaviateKeywordVectorizedHybridSearchTests_UnnamedVectors.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_UnnamedVectors.VectorAndStringFixture>,
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_UnnamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

        protected override string CollectionName => "VectorAndStringHybridSearch";
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

        protected override string CollectionName => "MultiTextHybridSearch";
    }
}
