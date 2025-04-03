// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using AzureAISearchIntegrationTests.Support;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.HybridSearch;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace AzureAISearchIntegrationTests.HybridSearch;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
public class AzureAISearchKeywordVectorizedHybridSearchTests(
    AzureAISearchKeywordVectorizedHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    AzureAISearchKeywordVectorizedHybridSearchTests.MultiTextFixture multiTextFixture)
    : KeywordVectorizedHybridSearchComplianceTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<AzureAISearchKeywordVectorizedHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<AzureAISearchKeywordVectorizedHybridSearchTests.MultiTextFixture>
{
#pragma warning disable CA1308 // Normalize strings to uppercase
    private static readonly string _testIndexPostfix = new Regex("[^a-zA-Z0-9]").Replace(Environment.MachineName.ToLowerInvariant(), "");
#pragma warning restore CA1308 // Normalize strings to uppercase

    public new class VectorAndStringFixture : KeywordVectorizedHybridSearchComplianceTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        protected override string CollectionName => "vecstring-hybrid-search-" + _testIndexPostfix;
    }

    public new class MultiTextFixture : KeywordVectorizedHybridSearchComplianceTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        protected override string CollectionName => "multitext-hybrid-search-" + _testIndexPostfix;
    }
}
