// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateKernelBuilderExtensions"/> class.
/// </summary>
public sealed class WeaviateKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<HttpClient>(Mock.Of<HttpClient>());

        // Act
        this._kernelBuilder.AddWeaviateVectorStore();

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<WeaviateVectorStore>(vectorStore);
    }

    [Fact]
    public void AddWeaviateVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost") };
        this._kernelBuilder.Services.AddSingleton<HttpClient>(httpClient);

        // Act
        this._kernelBuilder.AddWeaviateVectorStoreRecordCollection<TestRecord>("Testcollection");

        var kernel = this._kernelBuilder.Build();

        // Assert
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<Guid, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<WeaviateVectorStoreRecordCollection<Guid, TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<WeaviateVectorStoreRecordCollection<Guid, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Id { get; set; }
    }
}
