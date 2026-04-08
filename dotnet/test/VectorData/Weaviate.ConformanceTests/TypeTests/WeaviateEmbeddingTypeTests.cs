// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Weaviate.ConformanceTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace Weaviate.ConformanceTests.TypeTests;

public class WeaviateEmbeddingTypeTests(WeaviateEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<WeaviateEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
