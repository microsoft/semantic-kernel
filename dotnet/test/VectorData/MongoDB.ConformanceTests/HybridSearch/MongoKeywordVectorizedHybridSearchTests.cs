// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests.HybridSearch;

public class MongoKeywordVectorizedHybridSearchTests(
    MongoKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    MongoKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<MongoKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<MongoKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
