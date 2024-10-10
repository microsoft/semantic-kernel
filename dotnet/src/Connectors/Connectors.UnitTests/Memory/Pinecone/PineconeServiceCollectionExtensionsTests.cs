// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
=======
>>>>>>> Stashed changes
using System;
using Microsoft.Extensions.DependencyInjection;
<<<<<<< HEAD
using Microsoft.SemanticKernel;
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    private void AssertVectorStoreCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<PineconeVectorStore>(vectorStore);
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
