// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using Microsoft.Extensions.VectorData;
using Pgvector;
using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace PgVectorIntegrationTests;

public class PostgresEmbeddingTypeTests(PostgresEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<int>(fixture), IClassFixture<PostgresEmbeddingTypeTests.Fixture>
{
#if NET8_0_OR_GREATER
    [ConditionalFact]
    public virtual Task ReadOnlyMemory_of_Half()
        => this.Test<ReadOnlyMemory<Half>>(
            new ReadOnlyMemory<Half>([(byte)1, (byte)2, (byte)3]),
            new ReadOnlyMemoryEmbeddingGenerator<Half>(new([(byte)1, (byte)2, (byte)3])));
#endif

    // TODO: Figure out the embedding generation story for binaryvec/sparsevec - need an Embedding wrapper

    [ConditionalFact]
    public virtual Task BitArray()
        => this.Test<BitArray>(new BitArray([true, false, true]), distanceFunction: DistanceFunction.HammingDistance, embeddingGenerator: null);

    [ConditionalFact]
    public virtual Task SparseVector()
        => this.Test<SparseVector>(new SparseVector(new ReadOnlyMemory<float>([1, 2, 3])), embeddingGenerator: null);

    public new class Fixture : EmbeddingTypeTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
