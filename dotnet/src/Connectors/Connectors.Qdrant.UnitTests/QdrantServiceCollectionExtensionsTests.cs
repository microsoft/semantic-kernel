// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Tests for the <see cref="QdrantServiceCollectionExtensions"/> class.
/// </summary>
public class QdrantServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public QdrantServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        using var qdrantClient = new QdrantClient("localhost");
        this._serviceCollection.AddSingleton<QdrantClient>(qdrantClient);

        // Act.
        this._serviceCollection.AddQdrantVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithHostAndPortAndCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddQdrantVectorStore("localhost", 8080, true, "apikey");

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithHostRegistersClass()
    {
        // Act.
        this._serviceCollection.AddQdrantVectorStore("localhost");

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        using var qdrantClient = new QdrantClient("localhost");
        this._serviceCollection.AddSingleton<QdrantClient>(qdrantClient);

        // Act.
        this._serviceCollection.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithHostAndPortAndCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "localhost", 8080, true, "apikey");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithHostRegistersClass()
    {
        // Act.
        this._serviceCollection.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "localhost");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<QdrantVectorStore>(vectorStore);
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<QdrantVectorStoreRecordCollection<ulong, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<QdrantVectorStoreRecordCollection<ulong, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public ulong Id { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
