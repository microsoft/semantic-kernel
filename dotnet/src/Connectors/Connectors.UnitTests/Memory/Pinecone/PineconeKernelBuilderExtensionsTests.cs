// Copyright (c) Microsoft. All rights reserved.

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
using System;
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
using System;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System;
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Data;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.Connectors.UnitTests.Pinecone;

/// <summary>
/// Tests for the <see cref="PineconeKernelBuilderExtensions"/> class.
/// </summary>
public class PineconeKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public PineconeKernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        using var client = new Sdk.PineconeClient("fake api key");
        this._kernelBuilder.Services.AddSingleton<Sdk.PineconeClient>(client);

        // Act.
        this._kernelBuilder.AddPineconeVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithApiKeyRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddPineconeVectorStore("fake api key");

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
        this._kernelBuilder.Services.AddSingleton<Sdk.PineconeClient>(client);

        // Act.
        this._kernelBuilder.AddPineconeVectorStoreRecordCollection<TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithApiKeyRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddPineconeVectorStoreRecordCollection<TestRecord>("testcollection", "fake api key");

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
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
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
        var kernel = this._kernelBuilder.Build();

        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<PineconeVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorizedSearch<TestRecord>>();
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
