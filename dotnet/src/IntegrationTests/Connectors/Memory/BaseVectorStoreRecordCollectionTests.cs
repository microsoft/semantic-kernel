// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory;

/// <summary>
/// Base class for common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
/// <typeparam name="TKey">The type of key to use with the record collection.</typeparam>
public abstract class BaseVectorStoreRecordCollectionTests<TKey>
    where TKey : notnull
{
    protected abstract TKey Key1 { get; }
    protected abstract TKey Key2 { get; }
    protected abstract TKey Key3 { get; }
    protected abstract TKey Key4 { get; }

    protected abstract HashSet<string> GetSupportedDistanceFunctions();

    protected abstract IVectorStoreRecordCollection<TKey, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition) where TRecord : notnull;

    protected virtual int DelayAfterIndexCreateInMilliseconds { get; } = 0;

    protected virtual int DelayAfterUploadInMilliseconds { get; } = 0;

    [VectorStoreTheory]
    [InlineData(DistanceFunction.CosineDistance, 0, 2, 1, new int[] { 0, 2, 1 })]
    [InlineData(DistanceFunction.CosineSimilarity, 1, -1, 0, new int[] { 0, 2, 1 })]
    [InlineData(DistanceFunction.DotProductSimilarity, 1, -1, 0, new int[] { 0, 2, 1 })]
    [InlineData(DistanceFunction.EuclideanDistance, 0, 2, 1.73, new int[] { 0, 2, 1 })]
    [InlineData(DistanceFunction.EuclideanSquaredDistance, 0, 4, 3, new int[] { 0, 2, 1 })]
    [InlineData(DistanceFunction.Hamming, 0, 1, 3, new int[] { 0, 1, 2 })]
    [InlineData(DistanceFunction.ManhattanDistance, 0, 2, 3, new int[] { 0, 1, 2 })]
    public async Task VectorSearchShouldReturnExpectedScoresAsync(string distanceFunction, double expectedExactMatchScore, double expectedOppositeScore, double expectedOrthogonalScore, int[] resultOrder)
    {
        var keyDictionary = new Dictionary<int, TKey>
        {
            { 0, this.Key1 },
            { 1, this.Key2 },
            { 2, this.Key3 },
        };
        var scoreDictionary = new Dictionary<int, double>
        {
            { 0, expectedExactMatchScore },
            { 1, expectedOppositeScore },
            { 2, expectedOrthogonalScore },
        };

        // Don't test unsupported distance functions.
        var supportedDistanceFunctions = this.GetSupportedDistanceFunctions();
        if (!supportedDistanceFunctions.Contains(distanceFunction))
        {
            return;
        }

        // Arrange
        var definition = CreateKeyWithVectorRecordDefinition(4, distanceFunction);
        var sut = this.GetTargetRecordCollection<KeyWithVectorRecord<TKey>>(
            $"scorebydf{distanceFunction}",
            definition);

        await sut.CreateCollectionIfNotExistsAsync();
        await Task.Delay(this.DelayAfterIndexCreateInMilliseconds);

        // Create two vectors that are opposite to each other and records that use these
        // plus a further vector that is orthogonal to the base vector.
        var baseVector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        var oppositeVector = new ReadOnlyMemory<float>([-1, 0, 0, 0]);
        var orthogonalVector = new ReadOnlyMemory<float>([0f, -1f, -1f, 0f]);

        var baseRecord = new KeyWithVectorRecord<TKey>
        {
            Key = this.Key1,
            Vector = baseVector,
        };

        var oppositeRecord = new KeyWithVectorRecord<TKey>
        {
            Key = this.Key2,
            Vector = oppositeVector,
        };

        var orthogonalRecord = new KeyWithVectorRecord<TKey>
        {
            Key = this.Key3,
            Vector = orthogonalVector,
        };

        await sut.UpsertAsync([baseRecord, oppositeRecord, orthogonalRecord]);
        await Task.Delay(this.DelayAfterUploadInMilliseconds);

        // Act
        var results = await sut.SearchEmbeddingAsync(baseVector, top: 3).ToListAsync();

        // Assert
        Assert.Equal(3, results.Count);

        Assert.Equal(keyDictionary[resultOrder[0]], results[0].Record.Key);
        Assert.Equal(Math.Round(scoreDictionary[resultOrder[0]], 2), Math.Round(results[0].Score!.Value, 2));

        Assert.Equal(keyDictionary[resultOrder[1]], results[1].Record.Key);
        Assert.Equal(Math.Round(scoreDictionary[resultOrder[1]], 2), Math.Round(results[1].Score!.Value, 2));

        Assert.Equal(keyDictionary[resultOrder[2]], results[2].Record.Key);
        Assert.Equal(Math.Round(scoreDictionary[resultOrder[2]], 2), Math.Round(results[2].Score!.Value, 2));

        // Cleanup
        await sut.DeleteCollectionAsync();
    }

    private static VectorStoreRecordDefinition CreateKeyWithVectorRecordDefinition(int vectorDimensions, string distanceFunction)
    {
        var definition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), vectorDimensions) { DistanceFunction = distanceFunction },
            ],
        };

        return definition;
    }

    private sealed class KeyWithVectorRecord<TRecordKey>
    {
        public required TRecordKey Key { get; set; }

        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
