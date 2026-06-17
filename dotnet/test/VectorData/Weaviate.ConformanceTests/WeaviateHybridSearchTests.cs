// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateHybridSearchTests_NamedVectors(
    WeaviateHybridSearchTests_NamedVectors.VectorAndStringFixture vectorAndStringFixture,
    WeaviateHybridSearchTests_NamedVectors.MultiTextFixture multiTextFixture)
    : HybridSearchTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateHybridSearchTests_NamedVectors.VectorAndStringFixture>,
        IClassFixture<WeaviateHybridSearchTests_NamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }

    public new class MultiTextFixture : HybridSearchTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}

public class WeaviateHybridSearchTests_UnnamedVector(
    WeaviateHybridSearchTests_UnnamedVector.VectorAndStringFixture vectorAndStringFixture,
    WeaviateHybridSearchTests_UnnamedVector.MultiTextFixture multiTextFixture)
    : HybridSearchTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateHybridSearchTests_UnnamedVector.VectorAndStringFixture>,
        IClassFixture<WeaviateHybridSearchTests_UnnamedVector.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
    }

    public new class MultiTextFixture : HybridSearchTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
    }
}
