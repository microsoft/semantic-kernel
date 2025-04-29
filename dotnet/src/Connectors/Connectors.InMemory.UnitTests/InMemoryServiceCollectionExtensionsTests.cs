// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Xunit;

namespace SemanticKernel.Connectors.InMemory.UnitTests;

/// <summary>
/// Contains tests for the <see cref="InMemoryServiceCollectionExtensions"/> class.
/// </summary>
public class InMemoryServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public InMemoryServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Act.
        this._serviceCollection.AddInMemoryVectorStore();

        // Assert.
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<InMemoryVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Act.
        this._serviceCollection.AddInMemoryVectorStoreRecordCollection<string, TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<InMemoryVectorStoreRecordCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<InMemoryVectorStoreRecordCollection<string, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
