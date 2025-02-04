// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Filter;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosFilterFixture : FilterFixtureBase<string>
{
    public override async Task InitializeAsync()
    {
        await CosmosTestEnvironment.InitializeAsync();

        await base.InitializeAsync();
    }

    protected override IVectorStore GetVectorStore()
        => CosmosTestEnvironment.DefaultVectorStore;

    public override async Task DisposeAsync()
    {
        await base.DisposeAsync();
    }
}
