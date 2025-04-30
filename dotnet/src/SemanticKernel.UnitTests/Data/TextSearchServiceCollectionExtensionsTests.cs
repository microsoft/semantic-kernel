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
    public void AddVectorStoreTextSearch()
    {
        // Arrange
        using var embeddingGenerator = new MockTextEmbeddingGenerator();

        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act
        services.AddSingleton<IVectorSearch<DataModel>>(collection);
        services.AddSingleton<ITextSearchStringMapper>(stringMapper);
        services.AddSingleton<ITextSearchResultMapper>(resultMapper);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchWithNoMappers()
    {
        // Arrange
        using var embeddingGenerator = new MockTextEmbeddingGenerator();

        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");

        // Act
        services.AddSingleton<IVectorSearch<DataModel>>(collection);
        services.AddVectorStoreTextSearch<DataModel>();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchWithKeyedIVectorSearch()
    {
        // Arrange
        using var embeddingGenerator = new MockTextEmbeddingGenerator();

        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");

        // Act
        services.AddKeyedSingleton<IVectorSearch<DataModel>>("vs1", collection);
        services.AddVectorStoreTextSearch<DataModel>("vs1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedIVectorSearch()
    {
        // Arrange
        using var embeddingGenerator = new MockTextEmbeddingGenerator();

        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");

        // Act
        services.AddKeyedSingleton<IVectorSearch<DataModel>>("vs1", collection);
        services.AddVectorStoreTextSearch<DataModel>("vs2");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModel>>());
    }

#pragma warning disable CS0618 // Type or member is obsolete
    [Fact]
    public void AddVectorStoreTextSearchWithKeyedVectorSearchAndEmbeddingGenerationService()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var collection = vectorStore.GetCollection<Guid, DataModelWithRawEmbedding>("records");
        using var generator = new MockTextEmbeddingGenerator();

        // Act
        services.AddKeyedSingleton<IVectorSearch<DataModelWithRawEmbedding>>("vs1", collection);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", generator);

        services.AddVectorStoreTextSearch<DataModelWithRawEmbedding>("vs1", "tegs1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var result = serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModelWithRawEmbedding>>();
        Assert.NotNull(result);
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedVectorSearch()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var collection = vectorStore.GetCollection<Guid, DataModelWithRawEmbedding>("records");
        using var textGeneration = new MockTextEmbeddingGenerator();

        // Act
        services.AddKeyedSingleton<IVectorSearch<DataModelWithRawEmbedding>>("vs1", collection);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", textGeneration);

        services.AddVectorStoreTextSearch<DataModelWithRawEmbedding>("vs2", "tegs1");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModelWithRawEmbedding>>());
    }

    [Fact]
    public void AddVectorStoreTextSearchFailsMissingKeyedTextEmbeddingGenerationService()
    {
        // Arrange
        var services = new ServiceCollection();
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModelWithRawEmbedding>("records");
        using var textGeneration = new MockTextEmbeddingGenerator();

        // Act
        services.AddKeyedSingleton<IVectorSearch<DataModelWithRawEmbedding>>("vs1", vectorSearch);
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>("tegs1", textGeneration);

        services.AddVectorStoreTextSearch<DataModelWithRawEmbedding>("vs1", "tegs2");

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        Assert.Throws<InvalidOperationException>(() => serviceProvider.GetRequiredService<VectorStoreTextSearch<DataModelWithRawEmbedding>>());
    }
#pragma warning restore CS0618 // Type or member is obsolete
}
