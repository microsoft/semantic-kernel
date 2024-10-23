// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;
public class VectorStoreTextSearchTests : VectorStoreTextSearchTestBase
{
    [Fact]
    public void CanCreateVectorStoreTextSearchWithIVectorizedSearch()
    {
        // Arrange.
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act.
        var sut = new VectorStoreTextSearch<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService(), stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }

    [Fact]
    public void CanCreateVectorStoreTextSearchWithIVectorizableTextSearch()
    {
        // Arrange.
        var vectorStore = new InMemoryVectorStore();
        var vectorSearch = vectorStore.GetCollection<Guid, DataModel>("records");
        var vectorizableTextSearch = new VectorizedSearchWrapper<DataModel>(vectorSearch, new MockTextEmbeddingGenerationService());
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // Act.
        var sut = new VectorStoreTextSearch<DataModel>(vectorizableTextSearch, stringMapper, resultMapper);

        // Assert.
        Assert.NotNull(sut);
    }

    [Fact]
    public async Task CanSearchWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanSearchWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<string> searchResults = await sut.SearchAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetTextSearchResultsWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<TextSearchResult> searchResults = await sut.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanGetSearchResultsWithVectorizableTextSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizableTextSearchAsync();

        // Act.
        KernelSearchResults<object> searchResults = await sut.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 2, Skip = 0 });
        var results = await searchResults.Results.ToListAsync();

        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task CanFilterGetSearchResultsWithVectorizedSearchAsync()
    {
        // Arrange.
        var sut = await CreateVectorStoreTextSearchFromVectorizedSearchAsync();
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
}
