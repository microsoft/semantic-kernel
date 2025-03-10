// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.VectorSearch;

public abstract class VectorSearchDistanceFunctionComplianceTests<TKey>(VectorStoreFixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public virtual Task CosineDistance()
        => this.SimpleSearch(DistanceFunction.CosineDistance, 0, 2, 1, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task CosineSimilarity()
        => this.SimpleSearch(DistanceFunction.CosineSimilarity, 1, -1, 0, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task DotProductSimilarity()
        => this.SimpleSearch(DistanceFunction.DotProductSimilarity, 1, -1, 0, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task NegativeDotProductSimilarity()
        => this.SimpleSearch(DistanceFunction.NegativeDotProductSimilarity, -1, 1, 0, [1, 2, 0]);

    [ConditionalFact]
    public virtual Task EuclideanDistance()
        => this.SimpleSearch(DistanceFunction.EuclideanDistance, 0, 2, 1.73, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task EuclideanSquaredDistance()
        => this.SimpleSearch(DistanceFunction.EuclideanSquaredDistance, 0, 4, 3, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task Hamming()
        => this.SimpleSearch(DistanceFunction.Hamming, 0, 1, 3, [0, 1, 2]);

    [ConditionalFact]
    public virtual Task ManhattanDistance()
        => this.SimpleSearch(DistanceFunction.ManhattanDistance, 0, 2, 3, [0, 1, 2]);

    protected virtual string? IndexKind => null;

    protected async Task SimpleSearch(string distanceFunction, double expectedExactMatchScore,
        double expectedOppositeScore, double expectedOrthogonalScore, int[] resultOrder)
    {
        ReadOnlyMemory<float> baseVector = new([1, 0, 0, 0]);
        ReadOnlyMemory<float> oppositeVector = new([-1, 0, 0, 0]);
        ReadOnlyMemory<float> orthogonalVector = new([0f, -1f, -1f, 0f]);

        double[] scoreDictionary = [expectedExactMatchScore, expectedOppositeScore, expectedOrthogonalScore];

        List<SearchRecord> records =
        [
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 8,
                Vector = baseVector,
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 9,
                String = "bar",
                Vector = oppositeVector,
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 9,
                String = "foo",
                Vector = orthogonalVector,
            }
        ];

        // The record definition describes the distance function,
        // so we need a dedicated collection per test.
        string uniqueCollectionName = Guid.NewGuid().ToString();
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, SearchRecord>(
            uniqueCollectionName, this.GetRecordDefinition(distanceFunction));

        await collection.CreateCollectionAsync();

        await collection.CreateCollectionIfNotExistsAsync(); // just to make sure it's idempotent

        try
        {
            await collection.UpsertBatchAsync(records).ToArrayAsync();

            var searchResult = await collection.VectorizedSearchAsync(baseVector);
            var results = await searchResult.Results.ToListAsync();
            VerifySearchResults(resultOrder, scoreDictionary, records, results, includeVectors: false);

            searchResult = await collection.VectorizedSearchAsync(baseVector, new() { IncludeVectors = true });
            results = await searchResult.Results.ToListAsync();
            VerifySearchResults(resultOrder, scoreDictionary, records, results, includeVectors: true);
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }

        static void VerifySearchResults(int[] resultOrder, double[] scoreDictionary, List<SearchRecord> records,
            List<VectorSearchResult<SearchRecord>> results, bool includeVectors)
        {
            Assert.Equal(records.Count, results.Count);
            for (int i = 0; i < results.Count; i++)
            {
                Assert.Equal(records[resultOrder[i]].Key, results[i].Record.Key);
                Assert.Equal(records[resultOrder[i]].Int, results[i].Record.Int);
                Assert.Equal(records[resultOrder[i]].String, results[i].Record.String);
                Assert.Equal(Math.Round(scoreDictionary[resultOrder[i]], 2), Math.Round(results[i].Score!.Value, 2));

                if (includeVectors)
                {
                    Assert.Equal(records[resultOrder[i]].Vector.ToArray(), results[i].Record.Vector.ToArray());
                }
                else
                {
                    Assert.Equal(0, results[i].Record.Vector.Length);
                }
            }
        }
    }

    private VectorStoreRecordDefinition GetRecordDefinition(string distanceFunction)
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(SearchRecord.Key), typeof(TKey)),
                new VectorStoreRecordVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>))
                {
                    Dimensions = 4,
                    DistanceFunction = distanceFunction,
                    IndexKind = this.IndexKind
                },
                new VectorStoreRecordDataProperty(nameof(SearchRecord.Int), typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(SearchRecord.String), typeof(string)) { IsFilterable = true },
            ]
        };

    public class SearchRecord
    {
        public TKey Key { get; set; } = default!;
        public ReadOnlyMemory<float> Vector { get; set; }

        public int Int { get; set; }
        public string? String { get; set; }
    }
}
