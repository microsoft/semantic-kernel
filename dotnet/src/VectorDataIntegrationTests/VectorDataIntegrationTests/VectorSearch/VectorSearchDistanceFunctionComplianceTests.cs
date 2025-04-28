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
        double[] expectedScores =
        [
            scoreDictionary[resultOrder[0]],
            scoreDictionary[resultOrder[1]],
            scoreDictionary[resultOrder[2]]
        ];

        List<SearchRecord> insertedRecords =
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
        SearchRecord[] expectedRecords =
        [
            insertedRecords[resultOrder[0]],
            insertedRecords[resultOrder[1]],
            insertedRecords[resultOrder[2]]
        ];

        // The record definition describes the distance function,
        // so we need a dedicated collection per test.
        string uniqueCollectionName = fixture.GetUniqueCollectionName();
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, SearchRecord>(
            uniqueCollectionName, this.GetRecordDefinition(distanceFunction));

        await collection.CreateCollectionAsync();

        await collection.CreateCollectionIfNotExistsAsync(); // just to make sure it's idempotent

        try
        {
            await collection.UpsertAsync(insertedRecords);

            var searchResult = collection.SearchEmbeddingAsync(baseVector, top: 3);
            var results = await searchResult.ToListAsync();
            VerifySearchResults(expectedRecords, expectedScores, results, includeVectors: false);

            searchResult = collection.SearchEmbeddingAsync(baseVector, top: 3, new() { IncludeVectors = true });
            results = await searchResult.ToListAsync();
            VerifySearchResults(expectedRecords, expectedScores, results, includeVectors: true);

            for (int skip = 0; skip <= insertedRecords.Count; skip++)
            {
                for (int top = Math.Max(1, skip); top <= insertedRecords.Count; top++)
                {
                    searchResult = collection.SearchEmbeddingAsync(baseVector,
                        top: top,
                        new()
                        {
                            Skip = skip,
                            IncludeVectors = true
                        });
                    results = await searchResult.ToListAsync();

                    VerifySearchResults(
                        expectedRecords.Skip(skip).Take(top).ToArray(),
                        expectedScores.Skip(skip).Take(top).ToArray(),
                        results, includeVectors: true);
                }
            }
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }

        static void VerifySearchResults(SearchRecord[] expectedRecords, double[] expectedScores,
            List<VectorSearchResult<SearchRecord>> results, bool includeVectors)
        {
            Assert.Equal(expectedRecords.Length, results.Count);
            for (int i = 0; i < results.Count; i++)
            {
                Assert.Equal(expectedRecords[i].Key, results[i].Record.Key);
                Assert.Equal(expectedRecords[i].Int, results[i].Record.Int);
                Assert.Equal(expectedRecords[i].String, results[i].Record.String);
                Assert.Equal(Math.Round(expectedScores[i], 2), Math.Round(results[i].Score!.Value, 2));

                if (includeVectors)
                {
                    Assert.Equal(expectedRecords[i].Vector.ToArray(), results[i].Record.Vector.ToArray());
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
                new VectorStoreRecordVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>), 4)
                {
                    DistanceFunction = distanceFunction,
                    IndexKind = this.IndexKind
                },
                new VectorStoreRecordDataProperty(nameof(SearchRecord.Int), typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty(nameof(SearchRecord.String), typeof(string)) { IsIndexed = true },
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
