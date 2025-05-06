// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.VectorSearch;

public abstract class VectorSearchWithFilterConformanceTests<TKey>(VectorStoreFixture fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task SearchWithFilterShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var collectionName = fixture.GetUniqueCollectionName();
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, SearchRecord>(collectionName);

        List<SearchRecord>? results = null;

        // Act
        try
        {
            await collection.CreateCollectionIfNotExistsAsync();

            await collection.UpsertAsync(
            [
                new SearchRecord
                {
                    Key = fixture.GenerateNextKey<TKey>(),
                    Text = "apples",
                    Vector = new ReadOnlyMemory<float>([1f, 1f, 1f])
                },
                new SearchRecord
                {
                    Key = fixture.GenerateNextKey<TKey>(),
                    Text = "oranges",
                    Vector = new ReadOnlyMemory<float>([10f, 20f, 35f])
                }
            ]);

            var vectorSearchResults = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([10f, 20f, 35f]), 1, new()
            {
                Filter = r => r.Text == "apples"
            }).ToListAsync();

            results = [.. vectorSearchResults.Select(l => l.Record)];
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }

        // Assert
        Assert.Single(results);
        Assert.Equal("apples", results[0].Text);
    }

    private class SearchRecord
    {
        [VectorStoreKey]
        public TKey Key { get; set; } = default!;

        [VectorStoreData]
        public string? Text { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
