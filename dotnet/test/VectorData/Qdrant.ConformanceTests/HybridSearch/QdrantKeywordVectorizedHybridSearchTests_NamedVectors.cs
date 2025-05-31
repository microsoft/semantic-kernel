// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.HybridSearch;

public class QdrantKeywordVectorizedHybridSearchTests_NamedVectors(
    QdrantKeywordVectorizedHybridSearchTests_NamedVectors.VectorAndStringFixture vectorAndStringFixture,
    QdrantKeywordVectorizedHybridSearchTests_NamedVectors.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<ulong>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<QdrantKeywordVectorizedHybridSearchTests_NamedVectors.VectorAndStringFixture>,
        IClassFixture<QdrantKeywordVectorizedHybridSearchTests_NamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<ulong>.VectorAndStringFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<ulong>.MultiTextFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
