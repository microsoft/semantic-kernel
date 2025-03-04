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
/// Base class for common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
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

    protected virtual string? IndexKind { get; } = null;

    protected abstract IVectorStoreRecordCollection<TKey, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition);

    [VectorStoreFact]
    public async Task SearchShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwhybrid",
            this.KeyWithVectorAndStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            // All records have the same vector, but the third contains Grapes, so searching for
            // Grapes should return the third record first.
            var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Grapes"]);

            // Assert
            var results = await searchResult.Results.ToListAsync();
            Assert.Equal(3, results.Count);

            Assert.Equal(this.Key3, results[0].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [VectorStoreFact]
    public async Task SearchWithFilterShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwfilteredhybrid",
            this.KeyWithVectorAndStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            // All records have the same vector, but the second contains Oranges, however
            // adding the filter should limit the results to only the first.
            var options = new HybridSearchOptions
            {
                Filter = new VectorSearchFilter().EqualTo("Code", 1)
            };
            var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], options);

            // Assert
            var results = await searchResult.Results.ToListAsync();
            Assert.Single(results);

            Assert.Equal(this.Key1, results[0].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [VectorStoreFact]
    public async Task SearchWithTopShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwtophybrid",
            this.KeyWithVectorAndStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            // All records have the same vector, but the second contains Oranges, so the
            // second should be returned first.
            var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], new() { Top = 1 });

            // Assert
            var results = await searchResult.Results.ToListAsync();
            Assert.Single(results);

            Assert.Equal(this.Key2, results[0].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [VectorStoreFact]
    public async Task SearchWithSkipShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwskiphybrid",
            this.KeyWithVectorAndStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            // All records have the same vector, but the first and third contain healthy,
            // so when skipping the first two results, we should get the second record.
            var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["healthy"], new() { Skip = 2 });

            // Assert
            var results = await searchResult.Results.ToListAsync();
            Assert.Single(results);

            Assert.Equal(this.Key2, results[0].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [VectorStoreFact]
    public async Task SearchWithMultipleKeywordsShouldRankMatchedKeywordsHigherAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<KeyWithVectorAndStringRecord<TKey>>(
            "kwmultikeywordhybrid",
            this.KeyWithVectorAndStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<KeyWithVectorAndStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["tangy", "nourishing"]);

            // Assert
            var results = await searchResult.Results.ToListAsync();
            Assert.Equal(3, results.Count);

            Assert.True(results[0].Record.Key.Equals(this.Key1) || results[0].Record.Key.Equals(this.Key2));
            Assert.True(results[1].Record.Key.Equals(this.Key1) || results[1].Record.Key.Equals(this.Key2));
            Assert.Equal(this.Key3, results[2].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [VectorStoreFact]
    public async Task SearchWithMultiTextRecordSearchesRequestedFieldAsync()
    {
        // Arrange
        var sut = this.GetTargetRecordCollection<MultiSearchStringRecord<TKey>>(
            "kwmultitexthybrid",
            this.MultiSearchStringRecordDefinition);

        var hybridSearch = sut as IKeywordHybridSearch<MultiSearchStringRecord<TKey>>;

        try
        {
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);
            await this.CreateCollectionAndAddDataAsync(sut, vector);

            // Act
            var searchResult1 = await hybridSearch!.HybridSearchAsync(vector, ["Apples"], new() { AdditionalPropertyName = nameof(MultiSearchStringRecord<string>.Text2) });
            var searchResult2 = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], new() { AdditionalPropertyName = nameof(MultiSearchStringRecord<string>.Text2) });

            // Assert
            var results1 = await searchResult1.Results.ToListAsync();
            Assert.Equal(2, results1.Count);

            Assert.Equal(this.Key2, results1[0].Record.Key);
            Assert.Equal(this.Key1, results1[1].Record.Key);

            var results2 = await searchResult2.Results.ToListAsync();
            Assert.Equal(2, results2.Count);

            Assert.Equal(this.Key1, results2[0].Record.Key);
            Assert.Equal(this.Key2, results2[1].Record.Key);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
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

    private async Task CreateCollectionAndAddDataAsync(IVectorStoreRecordCollection<TKey, MultiSearchStringRecord<TKey>> sut, ReadOnlyMemory<float> vector)
    {
        await sut.CreateCollectionIfNotExistsAsync();
        await Task.Delay(this.DelayAfterIndexCreateInMilliseconds);

        var record1 = new MultiSearchStringRecord<TKey>
        {
            Key = this.Key1,
            Text1 = "Apples",
            Text2 = "Oranges",
            Vector = vector
        };
        var record2 = new MultiSearchStringRecord<TKey>
        {
            Key = this.Key2,
            Text1 = "Oranges",
            Text2 = "Apples",
            Vector = vector
        };

        await sut.UpsertBatchAsync([record1, record2]).ToListAsync();
        await Task.Delay(this.DelayAfterUploadInMilliseconds);
    }

    private VectorStoreRecordDefinition KeyWithVectorAndStringRecordDefinition => new()
    {
        Properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
            new VectorStoreRecordDataProperty("Text", typeof(string)) { IsFullTextSearchable = true },
            new VectorStoreRecordDataProperty("Code", typeof(int)) { IsFilterable = true },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = this.IndexKind },
        }
    };

    private sealed class KeyWithVectorAndStringRecord<TRecordKey>
    {
        public TRecordKey Key { get; set; } = default!;

        public string Text { get; set; } = string.Empty;

        public int Code { get; set; }

        public ReadOnlyMemory<float> Vector { get; set; }
    }

    private VectorStoreRecordDefinition MultiSearchStringRecordDefinition => new()
    {
        Properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
            new VectorStoreRecordDataProperty("Text1", typeof(string)) { IsFullTextSearchable = true },
            new VectorStoreRecordDataProperty("Text2", typeof(string)) { IsFullTextSearchable = true },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = this.IndexKind },
        }
    };

    private sealed class MultiSearchStringRecord<TRecordKey>
    {
        public TRecordKey Key { get; set; } = default!;

        public string Text1 { get; set; } = string.Empty;

        public string Text2 { get; set; } = string.Empty;

        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
