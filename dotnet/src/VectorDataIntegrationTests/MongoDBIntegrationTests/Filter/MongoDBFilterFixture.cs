// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;

namespace MongoDBIntegrationTests.Filter;

public class MongoDBFilterFixture : FilterFixtureBase<string>
{
    private MongoDBContainerWrapper _containerWrapper;

    public override async Task InitializeAsync()
    {
        this._containerWrapper = await MongoDBContainerWrapper.GetAsync();

        await base.InitializeAsync();

        // TODO: There seems to be some asynchronicity/race condition in the test data seeding.
        // TODO: This could be a result of a weak ReadConcern, but only 'local' seems to be support with vector search.
        await Task.Delay(1000);
    }

    protected override IVectorStore GetVectorStore()
        => this._containerWrapper.DefaultVectorStore;

    public override async Task DisposeAsync()
    {
        await this._containerWrapper.DisposeAsync();
        await base.DisposeAsync();
    }
}
