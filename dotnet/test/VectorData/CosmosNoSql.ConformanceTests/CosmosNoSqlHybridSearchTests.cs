// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlHybridSearchTests(
    CosmosNoSqlHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    CosmosNoSqlHybridSearchTests.MultiTextFixture multiTextFixture)
    : HybridSearchTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<CosmosNoSqlHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<CosmosNoSqlHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }

    public new class MultiTextFixture : HybridSearchTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
