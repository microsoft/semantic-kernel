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
/// Tests for the <see cref="QdrantKernelBuilderExtensions"/> class.
/// </summary>
public class QdrantKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public QdrantKernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        using var qdrantClient = new QdrantClient("localhost");
        this._kernelBuilder.Services.AddSingleton<QdrantClient>(qdrantClient);

        // Act.
        this._kernelBuilder.AddQdrantVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithHostAndPortAndCredsRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddQdrantVectorStore("localhost", 8080, true, "apikey");

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithHostRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddQdrantVectorStore("localhost");

        // Assert.
        this.AssertVectorStoreCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<QdrantVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        using var qdrantClient = new QdrantClient("localhost");
        this._kernelBuilder.Services.AddSingleton<QdrantClient>(qdrantClient);

        // Act.
        this._kernelBuilder.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithHostAndPortAndCredsRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "localhost", 8080, true, "apikey");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithHostRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddQdrantVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "localhost");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var kernel = this._kernelBuilder.Build();

        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<QdrantVectorStoreRecordCollection<ulong, TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorSearch<TestRecord>>();
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
