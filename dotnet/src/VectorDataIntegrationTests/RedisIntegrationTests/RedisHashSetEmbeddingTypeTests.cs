// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace RedisIntegrationTests;

public class RedisHashSetEmbeddingTypeTests(RedisHashSetEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<RedisHashSetEmbeddingTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task ReadOnlyMemory_of_double()
        => this.Test<ReadOnlyMemory<double>>(
            new ReadOnlyMemory<double>([1d, 2d, 3d]),
            new ReadOnlyMemoryEmbeddingGenerator<double>(new([1d, 2d, 3d])));

    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
