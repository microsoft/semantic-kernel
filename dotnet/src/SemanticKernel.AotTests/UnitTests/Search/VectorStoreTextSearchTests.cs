// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class VectorStoreTextSearchTests
{
    public static async Task GetTextSearchResultsAsync()
    {
        // Arrange
        var testData = new List<VectorSearchResult<DataModel>>
        {
            new(new DataModel { Key = "test-name", Text = "test-result", Link = "test-link" }, 0.5)
        };

        VectorStoreTextSearch<DataModel> textSearch = new(new MockVectorizableTextSearch<DataModel>(testData));

        // Act
        KernelSearchResults<TextSearchResult> searchResults = await textSearch.GetTextSearchResultsAsync("query");

        List<TextSearchResult> results = [];

        await foreach (TextSearchResult result in searchResults.Results)
        {
            results.Add(result);
        }

        // Assert
        Assert.AreEqual(1, results.Count);
        Assert.AreEqual("test-name", results[0].Name);
        Assert.AreEqual("test-result", results[0].Value);
        Assert.AreEqual("test-link", results[0].Link);
    }

    public static async Task AddVectorStoreTextSearch()
    {
        // Arrange
        var testData = new List<VectorSearchResult<DataModel>>
        {
            new(new DataModel { Key = "test-name", Text = "test-result", Link = "test-link" }, 0.5)
        };
        var vectorizableTextSearch = new MockVectorizableTextSearch<DataModel>(testData);
        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton<IVectorSearch<DataModel>>(vectorizableTextSearch);

        // Act
        serviceCollection.AddVectorStoreTextSearch<DataModel>();
        var textSearch = serviceCollection.BuildServiceProvider().GetService<VectorStoreTextSearch<DataModel>>();
        Assert.IsNotNull(textSearch);

        // Assert
        KernelSearchResults<TextSearchResult> searchResults = await textSearch.GetTextSearchResultsAsync("query");

        List<TextSearchResult> results = [];

        await foreach (TextSearchResult result in searchResults.Results)
        {
            results.Add(result);
        }

        // Assert
        Assert.AreEqual(1, results.Count);
        Assert.AreEqual("test-name", results[0].Name);
        Assert.AreEqual("test-result", results[0].Value);
        Assert.AreEqual("test-link", results[0].Link);
    }

    private sealed class DataModel
    {
        [TextSearchResultName]
        public required string Key { get; init; }

        [TextSearchResultValue]
        public required string Text { get; init; }

        [TextSearchResultLinkAttribute]
        public required string Link { get; init; }
    }
}
