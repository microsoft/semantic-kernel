// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Pgvector;
using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace PgVector.ConformanceTests.TypeTests;

public class PostgresEmbeddingTypeTests(PostgresEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<int>(fixture), IClassFixture<PostgresEmbeddingTypeTests.Fixture>
{
#if NET
    [ConditionalFact]
    public virtual Task ReadOnlyMemory_of_Half()
        => this.Test<ReadOnlyMemory<Half>>(
            new ReadOnlyMemory<Half>([(byte)1, (byte)2, (byte)3]),
            new ReadOnlyMemoryEmbeddingGenerator<Half>([(byte)1, (byte)2, (byte)3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Span.ToArray(), a.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Embedding_of_Half()
        => this.Test<Embedding<Half>>(
            new Embedding<Half>(new ReadOnlyMemory<Half>([(byte)1, (byte)2, (byte)3])),
            new ReadOnlyMemoryEmbeddingGenerator<Half>([(byte)1, (byte)2, (byte)3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector.Span.ToArray(), a.Vector.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Array_of_Half()
        => this.Test<Half[]>(
            [(byte)1, (byte)2, (byte)3],
            new ReadOnlyMemoryEmbeddingGenerator<Half>([(byte)1, (byte)2, (byte)3]));
#endif

    [ConditionalFact]
    public virtual Task BitArray()
        => this.Test<BitArray>(
            new BitArray([true, false, true]),
            new BinaryEmbeddingGenerator(new BitArray([true, false, true])),
            distanceFunction: DistanceFunction.HammingDistance);

    [ConditionalFact]
    public virtual Task BinaryEmbedding()
        => this.Test<BinaryEmbedding>(
            new BinaryEmbedding(new([true, false, true])),
            new BinaryEmbeddingGenerator(new BitArray([true, false, true])),
            distanceFunction: DistanceFunction.HammingDistance,
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector, a.Vector));

    [ConditionalFact]
    public virtual Task SparseVector()
        => this.Test<SparseVector>(new SparseVector(new ReadOnlyMemory<float>([1, 2, 3])), embeddingGenerator: null);

    // TODO: Figure out the embedding generation story for sparsevec - need an Embedding wrapper

    public new class Fixture : EmbeddingTypeTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
