// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace Redis.ConformanceTests;

public class RedisHashSetEmbeddingTypeTests(RedisHashSetEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<RedisHashSetEmbeddingTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task ReadOnlyMemory_of_double()
        => this.Test<ReadOnlyMemory<double>>(
            new ReadOnlyMemory<double>([1d, 2d, 3d]),
            new ReadOnlyMemoryEmbeddingGenerator<double>([1d, 2d, 3d]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Span.ToArray(), a.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Embedding_of_double()
        => this.Test<Embedding<double>>(
            new Embedding<double>(new ReadOnlyMemory<double>([1, 2, 3])),
            new ReadOnlyMemoryEmbeddingGenerator<double>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector.Span.ToArray(), a.Vector.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Array_of_double()
        => this.Test<double[]>(
            [1, 2, 3],
            new ReadOnlyMemoryEmbeddingGenerator<double>([1, 2, 3]));

    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
