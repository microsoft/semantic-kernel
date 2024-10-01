// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.UnitTests.Data;
public class TextSearchServiceCollectionExtensionsTests : VectorStoreTextSearchTestBase
{
    [Fact]
    public void AddVectorStoreTextSearchWithIVectorizableTextSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new VolatileVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());

        // Act
        services.AddSingleton<IVectorizableTextSearch<DataModel>>(vectorizableTextSearch);
        services.AddSingleton<ITextSearchStringMapper>(stringMapper);
        services.AddSingleton<ITextSearchResultMapper>(resultMapper);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchWithIVectorizedSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new VolatileVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var textGeneration = new MockTextEmbeddingGenerationService();

        // Act
        services.AddSingleton<IVectorizedSearch<DataModel>>(vectorSearch);
        services.AddSingleton<ITextEmbeddingGenerationService>(textGeneration);
        services.AddSingleton<ITextSearchStringMapper>(stringMapper);
        services.AddSingleton<ITextSearchResultMapper>(resultMapper);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }
}
