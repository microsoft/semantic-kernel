// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace SqlServerIntegrationTests.VectorSearch;

public class SqlServerBasicVectorSearchTests(SqlServerBasicVectorSearchTests.Fixture fixture)
    : BasicVectorSearchTests<int>(fixture), IClassFixture<SqlServerBasicVectorSearchTests.Fixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(() => base.CosineSimilarity());

    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(() => base.DotProductSimilarity());

    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(() => base.EuclideanSquaredDistance());

    public override Task Hamming() => Assert.ThrowsAsync<NotSupportedException>(() => base.Hamming());

    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(() => base.ManhattanDistance());

    public new class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
