// Copyright (c) Microsoft. All rights reserved.

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

    private void AssertVectorStoreCreated()
    {
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<PineconeVectorStore>(vectorStore);
    }
}
