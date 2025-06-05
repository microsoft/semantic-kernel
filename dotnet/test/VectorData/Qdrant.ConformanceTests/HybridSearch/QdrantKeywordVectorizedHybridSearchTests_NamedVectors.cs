// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.HybridSearch;

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
