// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace PostgresIntegrationTests.VectorSearch;

public class PostgresBasicVectorSearchTests(PostgresBasicVectorSearchTests.Fixture fixture)
    : BasicVectorSearchTests<int>(fixture), IClassFixture<PostgresBasicVectorSearchTests.Fixture>
{
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(() => base.EuclideanSquaredDistance());

    public override Task Hamming() => Assert.ThrowsAsync<NotSupportedException>(() => base.Hamming());

    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(() => base.NegativeDotProductSimilarity());

    public new class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
