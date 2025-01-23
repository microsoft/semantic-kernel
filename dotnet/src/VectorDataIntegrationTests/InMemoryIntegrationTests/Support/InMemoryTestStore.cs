// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

internal sealed class InMemoryTestStore : TestStore
{
    public static InMemoryTestStore Instance { get; } = new();

    private InMemoryVectorStore _vectorStore = new();

    public override IVectorStore DefaultVectorStore => this._vectorStore;

    private InMemoryTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this._vectorStore = new InMemoryVectorStore();

        return Task.CompletedTask;
    }
}
