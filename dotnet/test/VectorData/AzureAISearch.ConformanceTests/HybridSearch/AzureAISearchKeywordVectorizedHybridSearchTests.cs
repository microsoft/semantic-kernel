// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests.HybridSearch;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearchable{TRecord}"/>.
/// </summary>
public class AzureAISearchKeywordVectorizedHybridSearchTests(
    AzureAISearchKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    AzureAISearchKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<AzureAISearchKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<AzureAISearchKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "vecstring-hybrid-search-" + AzureAISearchTestEnvironment.TestIndexPostfix;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "multitext-hybrid-search-" + AzureAISearchTestEnvironment.TestIndexPostfix;
    }
}
