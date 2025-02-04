// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Filter;
using WeaviateIntegrationTests.Support;

namespace WeaviateIntegrationTests.Filter;

public class WeaviateFilterFixture : FilterFixtureBase<Guid>
{
    private WeaviateContainerWrapper _containerWrapper;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    public override async Task InitializeAsync()
    {
        this._containerWrapper = await WeaviateContainerWrapper.GetAsync();

        await base.InitializeAsync();
    }

    protected override IVectorStore GetVectorStore()
        => this._containerWrapper.DefaultVectorStore;

    public override async Task DisposeAsync()
    {
        await this._containerWrapper.DisposeAsync();
        await base.DisposeAsync();
    }
}
