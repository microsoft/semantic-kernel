// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.InMemory;
using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

internal sealed class InMemoryTestStore : TestStore
{
    public static InMemoryTestStore Instance { get; } = new();

    public InMemoryVectorStore GetVectorStore(InMemoryVectorStoreOptions options)
        => new(new() { EmbeddingGenerator = options.EmbeddingGenerator });

    private InMemoryTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this.DefaultVectorStore = new InMemoryVectorStore();

        return Task.CompletedTask;
    }
}
