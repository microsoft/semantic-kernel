// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.Core;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Tests for the <see cref="AzureAISearchServiceCollectionExtensions"/> class.
/// </summary>
public class AzureAISearchServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public AzureAISearchServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        this._serviceCollection.AddSingleton<SearchIndexClient>(Mock.Of<SearchIndexClient>());

        // Act.
        this._serviceCollection.AddAzureAISearchVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithUriAndCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddAzureAISearchVectorStore(new Uri("https://localhost"), new AzureKeyCredential("fakeKey"));

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreWithUriAndTokenCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddAzureAISearchVectorStore(new Uri("https://localhost"), Mock.Of<TokenCredential>());

        // Assert.
        this.AssertVectorStoreCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        this._serviceCollection.AddSingleton<SearchIndexClient>(Mock.Of<SearchIndexClient>());

        // Act.
        this._serviceCollection.AddAzureAISearchVectorStoreRecordCollection<TestRecord>("testcollection");

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithUriAndCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddAzureAISearchVectorStoreRecordCollection<TestRecord>("testcollection", new Uri("https://localhost"), new AzureKeyCredential("fakeKey"));

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithUriAndTokenCredsRegistersClass()
    {
        // Act.
        this._serviceCollection.AddAzureAISearchVectorStoreRecordCollection<TestRecord>("testcollection", new Uri("https://localhost"), Mock.Of<TokenCredential>());

        // Assert.
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureAISearchVectorStore>(vectorStore);
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<AzureAISearchVectorStoreRecordCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<AzureAISearchVectorStoreRecordCollection<string, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;
    }
}
