// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests.Filter;

public class AzureAISearchBasicQueryTests(AzureAISearchBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<AzureAISearchBasicQueryTests.Fixture>
{
    // Azure AI Search only supports search.in() over strings
    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "query-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;
    }
}
