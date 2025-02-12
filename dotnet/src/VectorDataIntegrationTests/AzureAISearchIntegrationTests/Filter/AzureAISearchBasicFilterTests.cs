// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace AzureAISearchIntegrationTests.Filter;

public class AzureAISearchBasicFilterTests(AzureAISearchFilterFixture fixture) : BasicFilterTestsBase<string>(fixture), IClassFixture<AzureAISearchFilterFixture>
{
    // Azure AI Search only supports search.in() over strings
    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());
}
