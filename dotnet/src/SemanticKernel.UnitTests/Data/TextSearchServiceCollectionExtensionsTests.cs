// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;
public class TextSearchServiceCollectionExtensionsTests : VectorStoreTextSearchTestBase
{
    [Fact]
    public void AddTextSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var textSearch = new MockTextSearch();

        // Act
        services.AddTextSearch(textSearch);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<ITextSearch>();
        Assert.Same(textSearch, result);
    }

    [Fact]
    public void AddVectorStoreTextSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new VolatileVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var vectorTextSearch = new VectorStoreTextSearch<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService(), stringMapper, resultMapper);

        // Act
        services.AddVectorStoreTextSearch(vectorTextSearch);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.Same(vectorTextSearch, result);
    }

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
}
