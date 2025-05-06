// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using CosmosNoSqlIntegrationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace CosmosNoSqlIntegrationTests;

public class CosmosNoSqlEmbeddingTypeTests(CosmosNoSqlEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<CosmosNoSqlEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
