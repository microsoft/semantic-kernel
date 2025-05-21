// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSqlIntegrationTests.HybridSearch;

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
