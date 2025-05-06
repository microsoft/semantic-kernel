// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace AzureAISearchIntegrationTests.Filter;

public class AzureAISearchBasicFilterTests(AzureAISearchBasicFilterTests.Fixture fixture)
    : BasicFilterTests<string>(fixture), IClassFixture<AzureAISearchBasicFilterTests.Fixture>
{
    // Azure AI Search only supports search.in() over strings
    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "filter-tests";
    }
}
