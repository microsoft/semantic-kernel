// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.HybridSearch;

public class WeaviateKeywordVectorizedHybridSearchTests(
    WeaviateKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    WeaviateKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.Instance;

        protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

        protected override string CollectionName => "VectorAndStringHybridSearch";
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.Instance;

        protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

        protected override string CollectionName => "MultiTextHybridSearch";
    }
}
