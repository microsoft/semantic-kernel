// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.Extensions.VectorData;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;

namespace RedisIntegrationTests.Filter;

public class RedisFilterFixture : FilterFixtureBase<string>
{
    private RedisContainerWrapper _containerWrapper;

    public override async Task InitializeAsync()
    {
        this._containerWrapper = await RedisContainerWrapper.GetAsync();

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
