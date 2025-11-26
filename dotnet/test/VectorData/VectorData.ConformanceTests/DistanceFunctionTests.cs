// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests;

public abstract class DistanceFunctionTests<TKey>(DistanceFunctionTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public virtual Task CosineDistance()
        => this.Test(DistanceFunction.CosineDistance, 0, 2, 1, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task CosineSimilarity()
        => this.Test(DistanceFunction.CosineSimilarity, 1, -1, 0, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task DotProductSimilarity()
        => this.Test(DistanceFunction.DotProductSimilarity, 1, -1, 0, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task NegativeDotProductSimilarity()
        => this.Test(DistanceFunction.NegativeDotProductSimilarity, -1, 1, 0, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task EuclideanDistance()
        => this.Test(DistanceFunction.EuclideanDistance, 0, 2, 1.73, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task EuclideanSquaredDistance()
        => this.Test(DistanceFunction.EuclideanSquaredDistance, 0, 4, 3, [0, 2, 1]);

    [ConditionalFact]
    public virtual Task HammingDistance()
        => this.Test(DistanceFunction.HammingDistance, 0, 1, 3, [0, 1, 2]);

    [ConditionalFact]
    public virtual Task ManhattanDistance()
        => this.Test(DistanceFunction.ManhattanDistance, 0, 2, 3, [0, 1, 2]);

    protected virtual async Task Test(
        string distanceFunction,
        double expectedExactMatchScore,
        double expectedOppositeScore,
        double expectedOrthogonalScore,
        int[] resultOrder)
    {
        using var collection = fixture.CreateCollection(distanceFunction);
        await collection.EnsureCollectionDeletedAsync();
        await collection.EnsureCollectionExistsAsync();

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
                Int = 1,
                Vector = baseVector,
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 2,
                Vector = oppositeVector,
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 3,
                Vector = orthogonalVector,
            }
        ];
        SearchRecord[] expectedRecords =
        [
            insertedRecords[resultOrder[0]],
            insertedRecords[resultOrder[1]],
            insertedRecords[resultOrder[2]]
        ];

        await collection.UpsertAsync(insertedRecords);

        await fixture.TestStore.WaitForDataAsync(collection, insertedRecords.Count, vectorSize: 4);

        var results = await collection.SearchAsync(baseVector, top: 3).ToListAsync();

        Assert.Equal(expectedRecords.Length, results.Count);
        for (int i = 0; i < results.Count; i++)
        {
            Assert.Equal(expectedRecords[i].Key, results[i].Record.Key);
            Assert.Equal(expectedRecords[i].Int, results[i].Record.Int);
            if (fixture.AssertScores)
            {
                Assert.Equal(Math.Round(expectedScores[i], 2), Math.Round(results[i].Score!.Value, 2));
            }
        }
    }

    public abstract class Fixture : VectorStoreFixture
    {
        protected virtual string CollectionNameBase => nameof(DistanceFunctionTests<int>);
        public virtual string CollectionName => this.TestStore.AdjustCollectionName(this.CollectionNameBase);

        protected virtual string? IndexKind => null;

        public virtual bool AssertScores { get; } = true;

        public virtual VectorStoreCollection<TKey, SearchRecord> CreateCollection(string distanceFunction)
        {
            VectorStoreCollectionDefinition definition = new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(SearchRecord.Key), typeof(TKey)),
                    new VectorStoreDataProperty(nameof(SearchRecord.Int), typeof(int)),
                    new VectorStoreVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>), dimensions: 4)
                    {
                        DistanceFunction = distanceFunction,
                        IndexKind = this.IndexKind ?? this.DefaultIndexKind
                    }
                ]
            };

            return this.TestStore.DefaultVectorStore.GetCollection<TKey, SearchRecord>(this.CollectionName, definition);
        }
    }

    public class SearchRecord
    {
        public TKey Key { get; set; } = default!;
        public int Int { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
