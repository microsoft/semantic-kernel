// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests;

public class QdrantHybridSearchTests_NamedVectors(
    QdrantHybridSearchTests_NamedVectors.VectorAndStringFixture vectorAndStringFixture,
    QdrantHybridSearchTests_NamedVectors.MultiTextFixture multiTextFixture)
    : HybridSearchTests<ulong>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<QdrantHybridSearchTests_NamedVectors.VectorAndStringFixture>,
        IClassFixture<QdrantHybridSearchTests_NamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<ulong>.VectorAndStringFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }

    public new class MultiTextFixture : HybridSearchTests<ulong>.MultiTextFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}

public class QdrantHybridSearchTests_UnnamedVectors(
    QdrantHybridSearchTests_UnnamedVectors.VectorAndStringFixture vectorAndStringFixture,
    QdrantHybridSearchTests_UnnamedVectors.MultiTextFixture multiTextFixture)
    : HybridSearchTests<ulong>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<QdrantHybridSearchTests_UnnamedVectors.VectorAndStringFixture>,
        IClassFixture<QdrantHybridSearchTests_UnnamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<ulong>.VectorAndStringFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }

    public new class MultiTextFixture : HybridSearchTests<ulong>.MultiTextFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }
}
