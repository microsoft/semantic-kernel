// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using PineconeIntegrationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace PineconeIntegrationTests;

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
