// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlEmbeddingTypeTests(CosmosNoSqlEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<CosmosNoSqlEmbeddingTypeTests.Fixture>
{
    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task ReadOnlyMemory_of_byte()
        => this.Test<ReadOnlyMemory<byte>>(
            new ReadOnlyMemory<byte>([1, 2, 3]),
            new ReadOnlyMemoryEmbeddingGenerator<byte>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Span.ToArray(), a.Span.ToArray()));

    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task Embedding_of_byte()
        => this.Test<Embedding<byte>>(
            new Embedding<byte>(new ReadOnlyMemory<byte>([1, 2, 3])),
            new ReadOnlyMemoryEmbeddingGenerator<byte>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector.Span.ToArray(), a.Vector.Span.ToArray()));

    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task Array_of_byte()
        => this.Test<byte[]>(
            [1, 2, 3],
            new ReadOnlyMemoryEmbeddingGenerator<byte>([1, 2, 3]));

    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task ReadOnlyMemory_of_sbyte()
        => this.Test<ReadOnlyMemory<sbyte>>(
            new ReadOnlyMemory<sbyte>([1, 2, 3]),
            new ReadOnlyMemoryEmbeddingGenerator<sbyte>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Span.ToArray(), a.Span.ToArray()));

    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task Embedding_of_sbyte()
        => this.Test<Embedding<sbyte>>(
            new Embedding<sbyte>(new ReadOnlyMemory<sbyte>([1, 2, 3])),
            new ReadOnlyMemoryEmbeddingGenerator<sbyte>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector.Span.ToArray(), a.Vector.Span.ToArray()));

    [ConditionalFact(Skip = "TODO: Figure out why int8/uint8 embeddings aren't working (float32 is working), #12079")]
    public virtual Task Array_of_sbyte()
        => this.Test<sbyte[]>(
            [1, 2, 3],
            new ReadOnlyMemoryEmbeddingGenerator<sbyte>([1, 2, 3]));

    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
