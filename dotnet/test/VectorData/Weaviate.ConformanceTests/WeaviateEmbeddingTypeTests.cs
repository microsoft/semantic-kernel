// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace WeaviateIntegrationTests;

public class WeaviateEmbeddingTypeTests(WeaviateEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<WeaviateEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
