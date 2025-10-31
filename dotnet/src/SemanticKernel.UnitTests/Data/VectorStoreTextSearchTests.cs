// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreTextSearchTests : VectorStoreTextSearchTestBase
{
#pragma warning disable CS0618 // VectorStoreTextSearch with ITextEmbeddingGenerationService is obsolete
    [Fact]
    public void CanCreateVectorStoreTextSearchWithEmbeddingGenerationService()
    {
        // Arrange.
        using var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModelWithRawEmbedding>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        using var embeddingGenerationService = new MockTextEmbeddingGenerator();

        // Act.
        var sut = new VectorStoreTextSearch<DataModelWithRawEmbedding>(vectorSearch, (ITextEmbeddingGenerationService)embeddingGenerationService, stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }
#pragma warning restore CS0618

    [Fact]
    public void CanCreateVectorStoreTextSearchWithIVectorSearch()
    {
        // Arrange.
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = new MockTextEmbeddingGenerator() });
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act.
        var sut = new VectorStoreTextSearch<DataModel>(vectorSearch, stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }

    [Fact]
    public async Task CanSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act.
        KernelSearchResults<DataModel> searchResults = await typeSafeInterface.GetSearchResultsAsync("What is the Semantic Kernel?", new TextSearchOptions<DataModel> { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
        Assert.All(results, result => Assert.IsType<DataModel>(result));
    }

    [Fact]
    public async Task CanSearchWithEmbeddingGeneratorAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGeneratorAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithEmbeddingGeneratorAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGeneratorAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithEmbeddingGeneratorAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGeneratorAsync();
        ITextSearch<DataModelWithRawEmbedding> typeSafeInterface = sut;

        // Act.
        KernelSearchResults<DataModelWithRawEmbedding> searchResults = await typeSafeInterface.GetSearchResultsAsync("What is the Semantic Kernel?", new TextSearchOptions<DataModelWithRawEmbedding> { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
        Assert.All(results, result => Assert.IsType<DataModelWithRawEmbedding>(result));
    }

#pragma warning disable CS0618 // VectorStoreTextSearch with ITextEmbeddingGenerationService is obsolete
    [Fact]
    public async Task CanSearchWithEmbeddingGenerationServiceAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGenerationServiceAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithEmbeddingGenerationServiceAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGenerationServiceAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithEmbeddingGenerationServiceAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchWithEmbeddingGenerationServiceAsync();

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }
#pragma warning restore CS0618 // VectorStoreTextSearch with ITextEmbeddingGenerationService is obsolete

    [Fact]
    public async Task CanFilterGetSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();
        TextSearchFilter evenFilter = new();
        evenFilter.Equality("Tag", "Even");
        TextSearchFilter oddFilter = new();
        oddFilter.Equality("Tag", "Odd");

        // Act.
        KernelSearchResults<object> evenSearchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
        {
            Top = 2,
            Skip = 0,
            Filter = evenFilter
        });
        var evenResults = await evenSearchResults.Results.ToListAsync();
        KernelSearchResults<object> oddSearchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
        {
            Top = 2,
            Skip = 0,
            Filter = oddFilter
        });
        var oddResults = await oddSearchResults.Results.ToListAsync();

        Assert.Equal(2, evenResults.Count);
        var result1 = evenResults[0] as DataModel;
        Assert.Equal("Even", result1?.Tag);
        var result2 = evenResults[1] as DataModel;
        Assert.Equal("Even", result2?.Tag);

        Assert.Equal(2, oddResults.Count);
        result1 = oddResults[0] as DataModel;
        Assert.Equal("Odd", result1?.Tag);
        result2 = oddResults[1] as DataModel;
        Assert.Equal("Odd", result2?.Tag);
    }

    #region Generic Interface Tests (ITextSearch<TRecord>)

    [Fact]
    public async Task LinqSearchAsync()
    {
        // Arrange - Create VectorStoreTextSearch<DataModel> (implements both interfaces)
        var sut = await CreateVectorStoreTextSearchAsync();

        // Cast to ITextSearch<TRecord> to use type-safe LINQ filtering
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Use generic interface with LINQ filter
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 5,
            Filter = r => r.Tag == "Even"
        };

        KernelSearchResults<string> searchResults = await typeSafeInterface.SearchAsync(
            "What is the Semantic Kernel?",
            searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Should return results (filtering applied at vector store level)
        Assert.NotEmpty(results);
    }

    [Fact]
    public async Task LinqGetTextSearchResultsAsync()
    {
        // Arrange
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Use generic interface with LINQ filter
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 5,
            Filter = r => r.Tag == "Odd"
        };

        KernelSearchResults<TextSearchResult> searchResults = await typeSafeInterface.GetTextSearchResultsAsync(
            "What is the Semantic Kernel?",
            searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert
        Assert.NotEmpty(results);
        Assert.All(results, result => Assert.NotNull(result.Value));
    }

    [Fact]
    public async Task LinqGetSearchResultsAsync()
    {
        // Arrange
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Use type-safe LINQ filtering with ITextSearch<TRecord>
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 5,
            Filter = r => r.Tag == "Even"
        };

        KernelSearchResults<DataModel> searchResults = await typeSafeInterface.GetSearchResultsAsync(
            "What is the Semantic Kernel?",
            searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Results should be strongly-typed DataModel objects with Tag == "Even"
        Assert.NotEmpty(results);
        Assert.All(results, result =>
        {
            Assert.Equal("Even", result.Tag); // Direct property access - no cast needed!
        });
    }

    [Fact]
    public async Task LinqFilterSimpleEqualityAsync()
    {
        // Arrange
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Simple equality filter
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 10,
            Filter = r => r.Tag == "Odd"
        };

        var searchResults = await typeSafeInterface.GetSearchResultsAsync("test", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - All results should have Tag == "Odd"
        Assert.NotEmpty(results);
        Assert.All(results.Cast<DataModel>(), dm => Assert.Equal("Odd", dm.Tag));
    }

    [Fact]
    public async Task LinqFilterComplexExpressionAsync()
    {
        // Arrange
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Complex LINQ expression with multiple conditions
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 10,
            Filter = r => r.Tag == "Even" && r.Text.Contains("Record")
        };

        var searchResults = await typeSafeInterface.GetSearchResultsAsync("test", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Results should match both conditions
        Assert.NotEmpty(results);
        Assert.All(results.Cast<DataModel>(), dm =>
        {
            Assert.Equal("Even", dm.Tag);
            Assert.Contains("Record", dm.Text);
        });
    }

    [Fact]
    public async Task LinqFilterCollectionContainsAsync()
    {
        // Arrange - Create collection with DataModelWithTags
        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModelWithTags>("records");
        await collection.EnsureCollectionExistsAsync();

        // Add test records with tags
        var records = new[]
        {
            new DataModelWithTags
            {
                Key = Guid.NewGuid(),
                Text = "First",
                Tag = "test",
                Tags = new[] { "important", "urgent" },
                Embedding = "First"
            },
            new DataModelWithTags
            {
                Key = Guid.NewGuid(),
                Text = "Second",
                Tag = "test",
                Tags = new[] { "normal", "routine" },
                Embedding = "Second"
            },
            new DataModelWithTags
            {
                Key = Guid.NewGuid(),
                Text = "Third",
                Tag = "test",
                Tags = new[] { "important", "routine" },
                Embedding = "Third"
            }
        };

        foreach (var record in records)
        {
            await collection.UpsertAsync(record);
        }

        var textSearch = new VectorStoreTextSearch<DataModelWithTags>(
            collection,
            new DataModelTextSearchStringMapper(),
            new DataModelTextSearchResultMapper());

        ITextSearch<DataModelWithTags> typeSafeInterface = textSearch;

        // Act - Use LINQ .Contains() for collection filtering
        var searchOptions = new TextSearchOptions<DataModelWithTags>
        {
            Top = 10,
            Filter = r => r.Tags.Contains("important")
        };

        var searchResults = await typeSafeInterface.GetSearchResultsAsync("test", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Should return 2 records with "important" tag
        Assert.Equal(2, results.Count);
        Assert.All(results.Cast<DataModelWithTags>(), dm =>
            Assert.Contains("important", dm.Tags));
    }

    [Fact]
    public async Task LinqFilterNullReturnsAllResultsAsync()
    {
        // Arrange
        var sut = await CreateVectorStoreTextSearchAsync();
        ITextSearch<DataModel> typeSafeInterface = sut;

        // Act - Use generic interface with null filter
        var searchOptions = new TextSearchOptions<DataModel>
        {
            Top = 10,
            Filter = null  // No filter
        };

        var searchResults = await typeSafeInterface.GetSearchResultsAsync("test", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Should return both "Even" and "Odd" records
        var dataModels = results.Cast<DataModel>().ToList();
        Assert.Contains(dataModels, dm => dm.Tag == "Even");
        Assert.Contains(dataModels, dm => dm.Tag == "Odd");
    }

    #endregion
}
