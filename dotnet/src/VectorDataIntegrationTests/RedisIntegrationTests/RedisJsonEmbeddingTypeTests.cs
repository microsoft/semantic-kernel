// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using RedisIntegrationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace RedisIntegrationTests;

public class RedisJsonEmbeddingTypeTests(RedisJsonEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<RedisJsonEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }
}
