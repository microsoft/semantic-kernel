// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace Qdrant.ConformanceTests.TypeTests;

public class QdrantEmbeddingTypeTests(QdrantEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<QdrantEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
