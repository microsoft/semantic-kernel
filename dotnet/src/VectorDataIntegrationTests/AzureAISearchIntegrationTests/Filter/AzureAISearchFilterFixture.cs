// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace AzureAISearchIntegrationTests.Filter;

public class AzureAISearchFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => AzureAISearchTestStore.Instance;

    // Azure AI search only supports lowercase letters, digits or dashes.
    protected override string StoreName => "filter-tests";

    public override async Task DisposeAsync()
        => await base.DisposeAsync();
}
