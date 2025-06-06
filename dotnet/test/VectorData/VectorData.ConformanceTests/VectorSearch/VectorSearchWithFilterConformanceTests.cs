// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.VectorSearch;

public abstract class VectorSearchWithFilterConformanceTests<TKey>(VectorStoreFixture fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task SearchWithFilterShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var collectionName = fixture.GetUniqueCollectionName();
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, VectorSearchWithFilterRecord>(collectionName);

        List<VectorSearchWithFilterRecord>? results = null;

        // Act
        try
        {
            await collection.EnsureCollectionExistsAsync();

            List<VectorSearchWithFilterRecord> records =
            [
                new VectorSearchWithFilterRecord
                {
                    Key = fixture.GenerateNextKey<TKey>(),
                    Text = "apples",
                    Vector = new ReadOnlyMemory<float>([1f, 1f, 1f])
                },
                new VectorSearchWithFilterRecord
                {
                    Key = fixture.GenerateNextKey<TKey>(),
                    Text = "oranges",
                    Vector = new ReadOnlyMemory<float>([10f, 20f, 35f])
                }
            ];

            await collection.UpsertAsync(records);

            await fixture.TestStore.WaitForDataAsync(collection, records.Count);

            var vectorSearchResults = await collection.SearchAsync(new ReadOnlyMemory<float>([10f, 20f, 35f]), 1, new()
            {
                Filter = r => r.Text == "apples"
            }).ToListAsync();

            results = [.. vectorSearchResults.Select(l => l.Record)];
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }

        // Assert
        Assert.Single(results);
        Assert.Equal("apples", results[0].Text);
    }

    public class VectorSearchWithFilterRecord
    {
        [VectorStoreKey]
        public TKey Key { get; set; } = default!;

        [VectorStoreData]
        public string? Text { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
