// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace Pinecone.ConformanceTests.TypeTests;

public class PineconeEmbeddingTypeTests(PineconeEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<PineconeEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "embedding-type-tests";
    }
}
