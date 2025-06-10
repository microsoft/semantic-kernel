// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests.HybridSearch;

public class CosmosNoSqlKeywordVectorizedHybridSearchTests(
    CosmosNoSqlKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    CosmosNoSqlKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<CosmosNoSqlKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<CosmosNoSqlKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
