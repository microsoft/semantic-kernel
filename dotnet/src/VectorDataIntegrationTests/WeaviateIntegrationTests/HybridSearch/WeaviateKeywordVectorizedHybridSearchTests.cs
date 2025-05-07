// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.HybridSearch;

public class WeaviateKeywordVectorizedHybridSearchTests_NamedVectors(
    WeaviateKeywordVectorizedHybridSearchTests_NamedVectors.VectorAndStringFixture vectorAndStringFixture,
    WeaviateKeywordVectorizedHybridSearchTests_NamedVectors.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_NamedVectors.VectorAndStringFixture>,
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_NamedVectors.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        public override string CollectionName => "VectorAndStringHybridSearch";
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        public override string CollectionName => "MultiTextHybridSearch";
    }
}

public class WeaviateKeywordVectorizedHybridSearchTests_UnnamedVector(
    WeaviateKeywordVectorizedHybridSearchTests_UnnamedVector.VectorAndStringFixture vectorAndStringFixture,
    WeaviateKeywordVectorizedHybridSearchTests_UnnamedVector.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<Guid>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_UnnamedVector.VectorAndStringFixture>,
        IClassFixture<WeaviateKeywordVectorizedHybridSearchTests_UnnamedVector.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.VectorAndStringFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        public override string CollectionName => "VectorAndStringHybridSearch";
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<Guid>.MultiTextFixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        public override string CollectionName => "MultiTextHybridSearch";
    }
}
