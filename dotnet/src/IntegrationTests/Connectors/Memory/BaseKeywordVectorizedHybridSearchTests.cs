// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.VectorSearch;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory;

/// <summary>
/// Base class for common integration tests that should pass for any <see cref="IKeywordVectorizedHybridSearch{TRecord}"/>.
/// </summary>
/// <typeparam name="TKey">The type of key to use with the record collection.</typeparam>
public abstract class BaseKeywordVectorizedHybridSearchTests<TKey>
    where TKey : notnull
{
    protected abstract TKey Key1 { get; }
    protected abstract TKey Key2 { get; }
    protected abstract TKey Key3 { get; }
    protected abstract TKey Key4 { get; }

    protected virtual int DelayAfterIndexCreateInMilliseconds { get; } = 0;

    protected virtual int DelayAfterUploadInMilliseconds { get; } = 0;

    protected abstract IVectorStoreRecordCollection<TKey, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition);

    [Fact]
    public async Task SearchShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwhybrid",
            null);

        var hybridSeach = sut as IKeywordVectorizedHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        await this.CreateCollectionAndAddDataAsync(sut, vector);

        // Act
        // All records have the same vector, but the third contains Grapes, so searching for
        // Grapes should return the third record first.
        var searchResult = await hybridSeach!.KeywordVectorizedHybridSearch(vector, "Grapes");

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Equal(3, results.Count);

        Assert.Equal(this.Key3, results[0].Record.Key);

        // Cleanup
        await sut.DeleteCollectionAsync();
    }

    [Fact]
    public async Task SearchWithFilterShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwfilteredhybrid",
            null);

        var hybridSeach = sut as IKeywordVectorizedHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        await this.CreateCollectionAndAddDataAsync(sut, vector);

        // Act
        // All records have the same vector, but the second contains Oranges, however
        // adding the filter should limit the results to only the first.
        var options = new KeywordVectorizedHybridSearchOptions
        {
            Filter = new VectorSearchFilter().EqualTo("Code", 1)
        };
        var searchResult = await hybridSeach!.KeywordVectorizedHybridSearch(vector, "Oranges", options);

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(this.Key1, results[0].Record.Key);

        // Cleanup
        await sut.DeleteCollectionAsync();
    }

    [Fact]
    public async Task SearchWithTopShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwtophybrid",
            null);

        var hybridSeach = sut as IKeywordVectorizedHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        await this.CreateCollectionAndAddDataAsync(sut, vector);

        // Act
        // All records have the same vector, but the second contains Oranges, so the
        // second should be returned first.
        var searchResult = await hybridSeach!.KeywordVectorizedHybridSearch(vector, "Oranges", new() { Top = 1 });

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(this.Key2, results[0].Record.Key);

        // Cleanup
        await sut.DeleteCollectionAsync();
    }

    [Fact]
    public async Task SearchWithSkipShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwskiphybrid",
            null);

        var hybridSeach = sut as IKeywordVectorizedHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
        await this.CreateCollectionAndAddDataAsync(sut, vector);

        // Act
        // All records have the same vector, but the first and third contain healthy,
        // so when skipping the first two results, we should get the second record.
        var searchResult = await hybridSeach!.KeywordVectorizedHybridSearch(vector, "healthy", new() { Skip = 2 });

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(this.Key2, results[0].Record.Key);

        // Cleanup
        await sut.DeleteCollectionAsync();
    }

    private async Task CreateCollectionAndAddDataAsync(IVectorStoreRecordCollection<TKey, KeyWithVectorAndStringRecord<TKey>> sut, ReadOnlyMemory<float> vector)
    {
        await sut.CreateCollectionIfNotExistsAsync();
        await Task.Delay(this.DelayAfterIndexCreateInMilliseconds);

        var record1 = new KeyWithVectorAndStringRecord<TKey>
        {
            Key = this.Key1,
            Text = "Apples are a healthy and nourishing snack",
            Vector = vector,
            Code = 1
        };
        var record2 = new KeyWithVectorAndStringRecord<TKey>
        {
            Key = this.Key2,
            Text = "Oranges are tangy and contain vitamin c",
            Vector = vector,
            Code = 2
        };
        var record3 = new KeyWithVectorAndStringRecord<TKey>
        {
            Key = this.Key3,
            Text = "Grapes are healthy, sweet and juicy",
            Vector = vector,
            Code = 3
        };

        await sut.UpsertBatchAsync([record1, record2, record3]).ToListAsync();
        await Task.Delay(this.DelayAfterUploadInMilliseconds);
    }

    private sealed class KeyWithVectorAndStringRecord<TRecordKey>
    {
        [VectorStoreRecordKey]
        public TRecordKey Key { get; set; } = default!;

        [VectorStoreRecordData(IsFullTextSearchable = true)]
        public string Text { get; set; } = string.Empty;

        [VectorStoreRecordData(IsFilterable = true)]
        public int Code { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
