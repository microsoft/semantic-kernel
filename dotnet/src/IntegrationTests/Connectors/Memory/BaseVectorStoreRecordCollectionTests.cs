// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
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

    protected abstract IVectorStoreRecordCollection<TKey, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition);

    protected virtual int DelayAfterIndexCreateInMilliseconds { get; } = 0;

    protected virtual int DelayAfterUploadInMilliseconds { get; } = 0;

    [Theory]
    [InlineData(DistanceFunction.CosineDistance, 0, 2)]
    [InlineData(DistanceFunction.CosineSimilarity, 1, -1)]
    [InlineData(DistanceFunction.DotProductSimilarity, 1, -1)]
    [InlineData(DistanceFunction.EuclideanDistance, 0, 2)]
    [InlineData(DistanceFunction.EuclideanSquaredDistance, 0, 4)]
    [InlineData(DistanceFunction.Hamming, 0, 1)]
    [InlineData(DistanceFunction.ManhattanDistance, 0, 2)]
    public async Task VectorSearchShouldReturnExpectedScoresAsync(string distanceFunction, double expectedExactMatchScore, double expectedOppositeScore)
    {
        // Don't test unsupported distance functions.
        var supportedDistanceFunctions = this.GetSupportedDistanceFunctions();
        if (!supportedDistanceFunctions.Contains(distanceFunction))
        {
            return;
        }

        // Arrange
        var definition = CreateKeyWithVectorRecordDefinition(4, distanceFunction);
        var sut = this.GetTargetRecordCollection<KeyWithVectorRecord<TKey>>(
            $"scorebydistancefunction{distanceFunction}",
            definition);

        await sut.CreateCollectionIfNotExistsAsync();
        await Task.Delay(this.DelayAfterIndexCreateInMilliseconds);

        // Create two vectors that are opposite to each other and records that use these.
        var baseVector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        var oppositeVector = new ReadOnlyMemory<float>([-1, 0, 0, 0]);

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

        await sut.UpsertBatchAsync([baseRecord, oppositeRecord]).ToListAsync();
        await Task.Delay(this.DelayAfterUploadInMilliseconds);

        // Act
        var searchResult = await sut.VectorizedSearchAsync(baseVector);

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Equal(2, results.Count);

        Assert.Equal(this.Key1, results[0].Record.Key);
        Assert.Equal(expectedExactMatchScore, results[0].Score);

        Assert.Equal(this.Key2, results[1].Record.Key);
        Assert.Equal(expectedOppositeScore, results[1].Score);

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
                new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = vectorDimensions, DistanceFunction = distanceFunction },
            ],
        };

        return definition;
    }

    private class KeyWithVectorRecord<TRecordKey>
    {
        public required TRecordKey Key { get; set; }

        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
