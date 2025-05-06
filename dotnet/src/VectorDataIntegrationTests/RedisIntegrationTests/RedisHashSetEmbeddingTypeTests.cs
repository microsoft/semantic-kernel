// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using RedisIntegrationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace RedisIntegrationTests;

public class RedisHashSetEmbeddingTypeTests(RedisHashSetEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<RedisHashSetEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
