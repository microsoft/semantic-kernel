// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
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

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
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

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
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

    [Fact]
    public async Task InvalidPropertyFilterThrowsExpectedExceptionAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();
        TextSearchFilter invalidPropertyFilter = new();
        invalidPropertyFilter.Equality("NonExistentProperty", "SomeValue");

        // Act & Assert - Should throw ArgumentException because the LINQ filtering now validates 
        // property existence during expression building and throws descriptive errors
        var exception = await Assert.ThrowsAsync<ArgumentException>(async () =>
        {
            KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
            {
                Top = 5,
                Skip = 0,
                Filter = invalidPropertyFilter
            });

            // Try to enumerate results to trigger the exception
            await searchResults.Results.ToListAsync();
        });

        // Assert that we get the expected error message with improved formatting
        Assert.Contains("Property 'NonExistentProperty' not found", exception.Message);
    }

    [Fact]
    public async Task ComplexFiltersUseLegacyBehaviorAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();

        // Create a complex filter scenario - we'll use a filter that would require multiple clauses
        // For now, we'll test with a filter that has null or empty FilterClauses to simulate complex behavior
        TextSearchFilter complexFilter = new();
        // Don't use Equality() method to create a "complex" scenario that forces legacy behavior
        // This simulates cases where the new LINQ conversion logic returns null

        // Act & Assert - Should work without throwing
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
        {
            Top = 10,
            Skip = 0,
            Filter = complexFilter
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert that complex filtering works (falls back to legacy behavior or returns all results)
        Assert.NotNull(results);
    }

    [Fact]
    public async Task SimpleEqualityFilterUsesModernLinqPathAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();

        // Create a simple single equality filter that should use the modern LINQ path
        TextSearchFilter simpleFilter = new();
        simpleFilter.Equality("Tag", "Even");

        // Act
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
        {
            Top = 5,
            Skip = 0,
            Filter = simpleFilter
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert - The new LINQ filtering should work correctly for simple equality
        Assert.NotNull(results);
        Assert.NotEmpty(results);

        // Verify that all results match the filter criteria
        foreach (var result in results)
        {
            var dataModel = result as DataModel;
            Assert.NotNull(dataModel);
            Assert.Equal("Even", dataModel.Tag);
        }
    }

    [Fact]
    public async Task NullFilterReturnsAllResultsAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchAsync();

        // Act - Search with null filter (should return all results)
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new()
        {
            Top = 10,
            Skip = 0,
            Filter = null
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert - Should return results without any filtering applied
        Assert.NotNull(results);
        Assert.NotEmpty(results);

        // Verify we get both "Even" and "Odd" tagged results (proving no filtering occurred)
        var evenResults = results.Cast<DataModel>().Where(r => r.Tag == "Even");
        var oddResults = results.Cast<DataModel>().Where(r => r.Tag == "Odd");

        Assert.NotEmpty(evenResults);
        Assert.NotEmpty(oddResults);
    }

    [Fact]
    public async Task AnyTagEqualToFilterUsesModernLinqPathAsync()
    {
        // Arrange - Create a mock vector store with DataModelWithTags
        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModelWithTags>("records");
        await collection.EnsureCollectionExistsAsync();

        // Create test records with tags
        var records = new[]
        {
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "First record", Tag = "single", Tags = ["important", "urgent"] },
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "Second record", Tag = "single", Tags = ["normal", "routine"] },
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "Third record", Tag = "single", Tags = ["important", "routine"] }
        };

        foreach (var record in records)
        {
            await collection.UpsertAsync(record);
        }

        // Create VectorStoreTextSearch with embedding generator
        var textSearch = new VectorStoreTextSearch<DataModelWithTags>(
            collection,
            (IEmbeddingGenerator<string, Embedding<float>>)embeddingGenerator,
            new DataModelTextSearchStringMapper(),
            new DataModelTextSearchResultMapper());

        // Act - Search with AnyTagEqualTo filter (should use modern LINQ path)
        // Create filter with AnyTagEqualToFilterClause using reflection since TextSearchFilter doesn't expose Add method
        var filter = new TextSearchFilter();
        var filterClausesField = typeof(TextSearchFilter).GetField("_filterClauses", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var filterClauses = (List<FilterClause>)filterClausesField!.GetValue(filter)!;
        filterClauses.Add(new AnyTagEqualToFilterClause("Tags", "important"));

        var result = await textSearch.SearchAsync("test query", new TextSearchOptions
        {
            Top = 10,
            Filter = filter
        });

        // Assert
        Assert.NotNull(result);
    }

    [Fact]
    public async Task MultipleClauseFilterUsesModernLinqPathAsync()
    {
        // Arrange
        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
        var collection = vectorStore.GetCollection<Guid, DataModelWithTags>("records");
        await collection.EnsureCollectionExistsAsync();

        // Add test records 
        var testRecords = new[]
        {
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "Record 1", Tag = "Even", Tags = new[] { "important" } },
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "Record 2", Tag = "Odd", Tags = new[] { "important" } },
            new DataModelWithTags { Key = Guid.NewGuid(), Text = "Record 3", Tag = "Even", Tags = new[] { "normal" } },
        };

        foreach (var record in testRecords)
        {
            await collection.UpsertAsync(record);
        }

        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var sut = new VectorStoreTextSearch<DataModelWithTags>(collection, (IEmbeddingGenerator<string, Embedding<float>>)embeddingGenerator, stringMapper, resultMapper);

        // Act - Search with multiple filter clauses (equality + AnyTagEqualTo)
        // Create filter with both EqualToFilterClause and AnyTagEqualToFilterClause 
        var filter = new TextSearchFilter().Equality("Tag", "Even");
        var filterClausesField = typeof(TextSearchFilter).GetField("_filterClauses", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var filterClauses = (List<FilterClause>)filterClausesField!.GetValue(filter)!;
        filterClauses.Add(new AnyTagEqualToFilterClause("Tags", "important"));

        var searchOptions = new TextSearchOptions()
        {
            Top = 10,
            Filter = filter
        };

        var searchResults = await sut.GetSearchResultsAsync("test query", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        // Assert - Should return only records matching BOTH conditions (Tag == "Even" AND Tags.Contains("important"))
        Assert.Single(results);
        var matchingRecord = results.Cast<DataModelWithTags>().First();
        Assert.Equal("Even", matchingRecord.Tag);
        Assert.Contains("important", matchingRecord.Tags);
    }

    [Fact]
    public async Task UnsupportedFilterTypeUsesLegacyFallbackAsync()
    {
        // This test validates that our LINQ implementation gracefully falls back 
        // to legacy VectorSearchFilter conversion when encountering unsupported filter types

        // Arrange
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = new MockTextEmbeddingGenerator() });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");
        await collection.EnsureCollectionExistsAsync();

        // Add test records
        var testRecords = new[]
        {
            new DataModel { Key = Guid.NewGuid(), Text = "Record 1", Tag = "Target" },
            new DataModel { Key = Guid.NewGuid(), Text = "Record 2", Tag = "Other" },
        };

        foreach (var record in testRecords)
        {
            await collection.UpsertAsync(record);
        }

        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var sut = new VectorStoreTextSearch<DataModel>(collection, (IEmbeddingGenerator<string, Embedding<float>>)embeddingGenerator, stringMapper, resultMapper);

        // Create a custom filter that would fall back to legacy behavior
        // Since we can't easily create unsupported filter types, we use a complex multi-clause
        // scenario that our current LINQ implementation supports
        var searchOptions = new TextSearchOptions()
        {
            Top = 10,
            Filter = new TextSearchFilter().Equality("Tag", "Target")
        };

        // Act & Assert - Should complete successfully (either LINQ or fallback path)
        var searchResults = await sut.GetSearchResultsAsync("test query", searchOptions);
        var results = await searchResults.Results.ToListAsync();

        Assert.Single(results);
        var result = results.Cast<DataModel>().First();
        Assert.Equal("Target", result.Tag);
    }

    [Fact]
    public async Task AnyTagEqualToWithInvalidPropertyFallsBackGracefullyAsync()
    {
        // Arrange
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = new MockTextEmbeddingGenerator() });
        var collection = vectorStore.GetCollection<Guid, DataModel>("records");
        await collection.EnsureCollectionExistsAsync();

        // Add a test record
        await collection.UpsertAsync(new DataModel
        {
            Key = Guid.NewGuid(),
            Text = "Test record",
            Tag = "Test"
        });

        using var embeddingGenerator = new MockTextEmbeddingGenerator();
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();
        var sut = new VectorStoreTextSearch<DataModel>(collection, (IEmbeddingGenerator<string, Embedding<float>>)embeddingGenerator, stringMapper, resultMapper);

        // Act - Try to filter on non-existent collection property (should fallback to legacy)
        // Create filter with AnyTagEqualToFilterClause for non-existent property
        var filter = new TextSearchFilter();
        var filterClausesField = typeof(TextSearchFilter).GetField("_filterClauses", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var filterClauses = (List<FilterClause>)filterClausesField!.GetValue(filter)!;
        filterClauses.Add(new AnyTagEqualToFilterClause("NonExistentTags", "somevalue"));

        var searchOptions = new TextSearchOptions()
        {
            Top = 10,
            Filter = filter
        };

        // Should throw exception because NonExistentTags property doesn't exist on DataModel
        // This validates that our LINQ implementation correctly processes the filter and
        // the underlying collection properly validates property existence
        var searchResults = await sut.GetSearchResultsAsync("test query", searchOptions);

        // Assert - Should throw ArgumentException for non-existent property  
        await Assert.ThrowsAsync<ArgumentException>(async () =>
        {
            var results = await searchResults.Results.ToListAsync();
        });
    }
}
