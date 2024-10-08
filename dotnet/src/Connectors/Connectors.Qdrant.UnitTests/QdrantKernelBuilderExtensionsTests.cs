// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Data;
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
}
