// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.Core;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Tests for the <see cref="AzureAISearchKernelBuilderExtensions"/> class.
/// </summary>
public class AzureAISearchKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public AzureAISearchKernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.Services.AddSingleton<SearchIndexClient>(Mock.Of<SearchIndexClient>());

        // Act.
        this._kernelBuilder.AddAzureAISearchVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithUriAndCredsRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddAzureAISearchVectorStore(new Uri("https://localhost"), new AzureKeyCredential("fakeKey"));

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithUriAndTokenCredsRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddAzureAISearchVectorStore(new Uri("https://localhost"), Mock.Of<TokenCredential>());

        // Assert.
        this.AssertVectorStoreCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureAISearchVectorStore>(vectorStore);
    }
}
