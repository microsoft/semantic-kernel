// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;

namespace QdrantIntegrationTests.Filter;

public class QdrantFilterFixture : FilterFixtureBase<ulong>
{
    private QdrantContainerWrapper _containerWrapper;

    // Qdrant doesn't support the default Flat index kind
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;

    public override async Task InitializeAsync()
    {
        this._containerWrapper = await QdrantContainerWrapper.GetAsync();

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
