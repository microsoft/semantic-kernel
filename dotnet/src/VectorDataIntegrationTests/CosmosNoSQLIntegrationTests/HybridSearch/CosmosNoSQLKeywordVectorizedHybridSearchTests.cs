// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSQLIntegrationTests.HybridSearch;

public class CosmosNoSQLKeywordVectorizedHybridSearchTests(
    CosmosNoSQLKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    CosmosNoSQLKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<CosmosNoSQLKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<CosmosNoSQLKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
    }
}
