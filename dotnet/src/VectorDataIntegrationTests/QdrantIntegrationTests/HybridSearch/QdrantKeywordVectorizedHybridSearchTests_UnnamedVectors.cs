// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.HybridSearch;

public class QdrantKeywordVectorizedHybridSearchTests_UnnamedVectors(
    QdrantKeywordVectorizedHybridSearchTests_UnnamedVectors.VectorAndStringFixture vectorAndStringFixture,
    QdrantKeywordVectorizedHybridSearchTests_UnnamedVectors.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<ulong>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<QdrantKeywordVectorizedHybridSearchTests_UnnamedVectors.VectorAndStringFixture>,
        IClassFixture<QdrantKeywordVectorizedHybridSearchTests_UnnamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<ulong>.VectorAndStringFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<ulong>.MultiTextFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }
}
