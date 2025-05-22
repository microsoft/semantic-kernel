// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace PgVectorIntegrationTests.VectorSearch;

public class PostgresVectorSearchDistanceFunctionComplianceTests(PostgresFixture fixture) : VectorSearchDistanceFunctionComplianceTests<int>(fixture), IClassFixture<PostgresFixture>
{
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);

    public override async Task HammingDistance()
    {
        // Hamming distance is supported by pgvector, but only on binaray vectors (bit(x)), and the test uses float32 vectors (vector(x)).
        var exception = await Assert.ThrowsAsync<VectorStoreException>(base.HammingDistance);
        Assert.IsType<Npgsql.PostgresException>(exception.InnerException);
    }

    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
}
