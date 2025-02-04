// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using VectorDataSpecificationTests.Filter;

namespace PostgresIntegrationTests.Filter;

public class InMemoryFilterFixture : FilterFixtureBase<int>
{
    private readonly InMemoryVectorStore _vectorStore = new();

    protected override IVectorStore GetVectorStore()
        => this._vectorStore;
}
