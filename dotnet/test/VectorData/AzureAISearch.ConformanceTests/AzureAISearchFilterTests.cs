// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchFilterTests(AzureAISearchFilterTests.Fixture fixture)
    : FilterTests<string>(fixture), IClassFixture<AzureAISearchFilterTests.Fixture>
{
    // Azure AI Search only supports search.in() over strings
    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public new class Fixture : FilterTests<string>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "filter-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;
    }
}
