// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace MongoDBIntegrationTests.HybridSearch;

public class MongoDBKeywordVectorizedHybridSearchTests(
    MongoDBKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    MongoDBKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<MongoDBKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<MongoDBKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => MongoDBTestStore.Instance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => MongoDBTestStore.Instance;
    }
}
