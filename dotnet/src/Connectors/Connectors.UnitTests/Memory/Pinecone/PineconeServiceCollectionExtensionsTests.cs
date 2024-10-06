// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
<<<<<<< HEAD
using Microsoft.SemanticKernel;
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Data;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.Connectors.UnitTests.Pinecone;

/// <summary>
/// Tests for the <see cref="PineconeServiceCollectionExtensions"/> class.
/// </summary>
public class PineconeServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public PineconeServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        using var client = new Sdk.PineconeClient("fake api key");
        this._serviceCollection.AddSingleton<Sdk.PineconeClient>(client);

        // Act.
        this._serviceCollection.AddPineconeVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithApiKeyRegistersClass()
    {
        // Act.
        this._serviceCollection.AddPineconeVectorStore("fake api key");

        // Assert.
        this.AssertVectorStoreCreated();
    }
    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        using var client = new Sdk.PineconeClient("fake api key");
        this._serviceCollection.AddSingleton<Sdk.PineconeClient>(client);

        // Act.
        this._serviceCollection.AddPineconeVectorStoreRecordCollection<TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithApiKeyRegistersClass()
    {
        // Act.
        this._serviceCollection.AddPineconeVectorStoreRecordCollection<TestRecord>("testcollection", "fake api key");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<PineconeVectorStore>(vectorStore);
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<PineconeVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<PineconeVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
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
