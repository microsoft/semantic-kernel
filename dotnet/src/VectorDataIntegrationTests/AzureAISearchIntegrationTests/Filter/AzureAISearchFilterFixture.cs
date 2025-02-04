// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Filter;

namespace AzureAISearchIntegrationTests.Filter;

public class AzureAISearchFilterFixture : FilterFixtureBase<string>
{
    // Azure AI search only supports lowercase letters, digits or dashes.
    protected override string StoreName => "filter-tests";

    public override async Task InitializeAsync()
    {
        await AzureAISearchTestEnvironment.InitializeAsync();

        await base.InitializeAsync();

        // TODO: There seems to be some asynchronicity/race condition in the test data seeding.
        await Task.Delay(1000);
    }

    protected override IVectorStore GetVectorStore()
        => AzureAISearchTestEnvironment.DefaultVectorStore;

    public override async Task DisposeAsync()
    {
        await base.DisposeAsync();
    }
}
