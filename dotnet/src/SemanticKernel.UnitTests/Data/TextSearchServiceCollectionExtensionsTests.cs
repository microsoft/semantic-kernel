// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.InMemory;
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
        var vectorStore = new InMemoryVectorStore();
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
        var vectorStore = new InMemoryVectorStore();
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

    [Fact]
    public void AddVectorStoreTextSearchWithIVectorizableTextSearchAndNoMappers()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());

        // Act
        services.AddSingleton<IVectorizableTextSearch<DataModel>>(vectorizableTextSearch);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchWithIVectorizedSearchAndNoMappers()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var textGeneration = new MockTextEmbeddingGenerationService();

        // Act
        services.AddSingleton<IVectorizedSearch<DataModel>>(vectorSearch);
        services.AddSingleton<ITextEmbeddingGenerationService>(textGeneration);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchWithKeyedIVectorizableTextSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var vectorizableTextSearch1 = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());

        // Act
        services.AddKeyedSingleton<IVectorizableTextSearch<DataModel>>("vts1", vectorizableTextSearch1);
        services.AddVectorStoreTextSearch<DataModel>("vts1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedVectorizableTextSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var vectorizableTextSearch1 = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());

        // Act
        services.AddKeyedSingleton<IVectorizableTextSearch<DataModel>>("vts1", vectorizableTextSearch1);
        services.AddVectorStoreTextSearch<DataModel>("vts2");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>());
    }

    [Fact]
    public void AddVectorStoreTextSearchWithKeyedIVectorizedSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var textGeneration = new MockTextEmbeddingGenerationService();

        // Act
        services.AddKeyedSingleton<IVectorizedSearch<DataModel>>("vs1", vectorSearch);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", textGeneration);

        services.AddVectorStoreTextSearch<DataModel>("vs1", "tegs1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedVectorizedSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var textGeneration = new MockTextEmbeddingGenerationService();

        // Act
        services.AddKeyedSingleton<IVectorizedSearch<DataModel>>("vs1", vectorSearch);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", textGeneration);

        services.AddVectorStoreTextSearch<DataModel>("vs2", "tegs1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>());
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedTextEmbeddingGenerationService()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var textGeneration = new MockTextEmbeddingGenerationService();

        // Act
        services.AddKeyedSingleton<IVectorizedSearch<DataModel>>("vs1", vectorSearch);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", textGeneration);

        services.AddVectorStoreTextSearch<DataModel>("vs1", "tegs2");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>());
    }
}
