// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlTypes;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace SqlServer.ConformanceTests;

public class SqlServerEmbeddingTypeTests(SqlServerEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<SqlServerEmbeddingTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task SqlVector_of_float()
        => this.Test<SqlVector<float>>(
            new SqlVector<float>(new float[] { 1, 2, 3 }),
            new ReadOnlyMemoryEmbeddingGenerator<float>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Memory.ToArray(), a.Memory.ToArray()));

    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
