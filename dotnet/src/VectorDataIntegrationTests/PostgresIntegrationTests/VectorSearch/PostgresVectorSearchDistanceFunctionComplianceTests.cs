// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace PostgresIntegrationTests.VectorSearch;

public class PostgresVectorSearchDistanceFunctionComplianceTests(PostgresFixture fixture) : VectorSearchDistanceFunctionComplianceTests<int>(fixture), IClassFixture<PostgresFixture>
{
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);

    public override Task Hamming() => Assert.ThrowsAsync<NotSupportedException>(base.Hamming);

    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
}
