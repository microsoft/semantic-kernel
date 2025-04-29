// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

internal sealed class InMemoryTestStore : TestStore
{
    public static InMemoryTestStore Instance { get; } = new();

    private InMemoryVectorStore _defaultVectorStore = new();

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore;

    public InMemoryVectorStore GetVectorStore(InMemoryVectorStoreOptions options)
        => new(new() { EmbeddingGenerator = options.EmbeddingGenerator });

    private InMemoryTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this._defaultVectorStore = new InMemoryVectorStore();

        return Task.CompletedTask;
    }
}
