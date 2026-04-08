// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresDistanceFunctionTests(PostgresDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<int>(fixture), IClassFixture<PostgresDistanceFunctionTests.Fixture>
{
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);

    public override async Task HammingDistance()
    {
        // Hamming distance is supported by pgvector, but only on binary vectors (bit(x)), and the test uses float32 vectors (vector(x)).
        var exception = await Assert.ThrowsAsync<VectorStoreException>(base.HammingDistance);
        Assert.IsType<Npgsql.PostgresException>(exception.InnerException);
    }

    public new class Fixture() : DistanceFunctionTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
