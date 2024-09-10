// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Data;
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
}
