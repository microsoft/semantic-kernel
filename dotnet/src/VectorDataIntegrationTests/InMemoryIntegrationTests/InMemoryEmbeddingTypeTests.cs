// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace InMemoryIntegrationTests;

public class InMemoryEmbeddingTypeTests(InMemoryEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<InMemoryEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;

        public override bool RecreateCollection => true;
        public override bool AssertNoVectorsLoadedWithEmbeddingGeneration => false;
    }
}
