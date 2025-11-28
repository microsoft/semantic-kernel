// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests;

/// <summary>
/// Base class for common integration tests that should pass for any <see cref="IKeywordHybridSearchable{TRecord}"/>.
/// </summary>
/// <typeparam name="TKey">The type of key to use with the record collection.</typeparam>
public abstract class HybridSearchTests<TKey>(
    HybridSearchTests<TKey>.VectorAndStringFixture vectorAndStringFixture,
    HybridSearchTests<TKey>.MultiTextFixture multiTextFixture)
    where TKey : notnull
{
    [ConditionalFact]
    public async Task HybridSearchAsync()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the third contains Grapes, so searching for
        // Grapes should return the third record first.
        var results = await vectorAndStringFixture.HybridSearchable.HybridSearchAsync(vector, ["Grapes"], top: 3).ToListAsync();

        // Assert
        Assert.Equal(3, results.Count);
        Assert.Equal(3, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task HybridSearchAsync_with_filter()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the second contains Oranges, however
        // adding the filter should limit the results to only the first.
        var results = await vectorAndStringFixture.HybridSearchable
            .HybridSearchAsync(
                vector,
                ["Oranges"],
                top: 3,
                new() { Filter = r => r.Code == 1 })
            .ToListAsync();

        // Assert
        Assert.Equal(1, Assert.Single(results).Record.Code);
    }

    [ConditionalFact]
    public async Task HybridSearchAsync_with_top()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the second contains Oranges, so the
        // second should be returned first.
        var results = await vectorAndStringFixture.HybridSearchable.HybridSearchAsync(vector, ["Oranges"], top: 1).ToListAsync();

        // Assert
        Assert.Single(results);

        Assert.Equal(2, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task HybridSearchAsync_with_Skip()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the first and third contain healthy,
        // so when skipping the first two results, we should get the second record.
        var results = await vectorAndStringFixture.HybridSearchable.HybridSearchAsync(vector, ["healthy"], top: 3, new() { Skip = 2 }).ToListAsync();

        // Assert
        Assert.Single(results);

        Assert.Equal(2, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task HybridSearchAsync_with_multiple_keywords_ranks_matched_keywords_higher()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        var results = await vectorAndStringFixture.HybridSearchable.HybridSearchAsync(vector, ["tangy", "nourishing"], top: 3).ToListAsync();

        // Assert
        Assert.Equal(3, results.Count);

        Assert.True(results[0].Record.Code.Equals(1) || results[0].Record.Code.Equals(2));
        Assert.True(results[1].Record.Code.Equals(1) || results[1].Record.Code.Equals(2));
        Assert.Equal(3, results[2].Record.Code);
    }

    [ConditionalFact]
    public async Task HybridSearchAsync_with_multiple_text_properties()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        var results1 = await multiTextFixture.HybridSearchable
            .HybridSearchAsync(vector, ["Apples"], top: 4, new() { AdditionalProperty = r => r.Text2 })
            .ToListAsync();
        var results2 = await multiTextFixture.HybridSearchable
            .HybridSearchAsync(vector, ["Oranges"], top: 4, new() { AdditionalProperty = r => r.Text2 })
            .ToListAsync();

        // Assert
        Assert.Equal(2, results1.Count);

        Assert.Equal(2, results1[0].Record.Code);
        Assert.Equal(1, results1[1].Record.Code);

        Assert.Equal(2, results2.Count);

        Assert.Equal(1, results2[0].Record.Code);
        Assert.Equal(2, results2[1].Record.Code);
    }

    [ConditionalFact]
    public Task HybridSearchAsync_without_explicitly_specified_property_fails()
        => Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await multiTextFixture.HybridSearchable
                .HybridSearchAsync(new ReadOnlyMemory<float>([1, 0, 0, 0]), ["Apples"], top: 3)
                .ToListAsync());

    public sealed class VectorAndStringRecord<TRecordKey> : TestRecord<TKey>
    {
        public string Text { get; set; } = string.Empty;
        public int Code { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }

    public sealed class MultiTextStringRecord<TRecordKey> : TestRecord<TKey>
    {
        public string Text1 { get; set; } = string.Empty;
        public string Text2 { get; set; } = string.Empty;
        public int Code { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }

    public abstract class VectorAndStringFixture : VectorStoreCollectionFixture<TKey, VectorAndStringRecord<TKey>>
    {
        protected override string CollectionNameBase => "HybridSearchTests";

        public IKeywordHybridSearchable<VectorAndStringRecord<TKey>> HybridSearchable
            => (IKeywordHybridSearchable<VectorAndStringRecord<TKey>>)this.Collection;

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(TKey)),
                    new VectorStoreDataProperty("Text", typeof(string)) { IsFullTextIndexed = true },
                    new VectorStoreDataProperty("Code", typeof(int)) { IsIndexed = true },
                    new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 4) { IndexKind = this.IndexKind },
                ]
            };

        protected override List<VectorAndStringRecord<TKey>> BuildTestData()
        {
            // All records have the same vector - this fixture is about testing the full text search portion of hybrid search
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

            return
            [
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Text = "Apples are a healthy and nourishing snack",
                    Vector = vector,
                    Code = 1
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Text = "Oranges are tangy and contain vitamin c",
                    Vector = vector,
                    Code = 2
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Text = "Grapes are healthy, sweet and juicy",
                    Vector = vector,
                    Code = 3
                }
            ];
        }

        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, vectorSize: 4);
    }

    public abstract class MultiTextFixture : VectorStoreCollectionFixture<TKey, MultiTextStringRecord<TKey>>
    {
        protected override string CollectionNameBase => "MultiTextHybridSearchTests";

        public IKeywordHybridSearchable<MultiTextStringRecord<TKey>> HybridSearchable
            => (IKeywordHybridSearchable<MultiTextStringRecord<TKey>>)this.Collection;

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(TKey)),
                    new VectorStoreDataProperty("Text1", typeof(string)) { IsFullTextIndexed = true },
                    new VectorStoreDataProperty("Text2", typeof(string)) { IsFullTextIndexed = true },
                    new VectorStoreDataProperty("Code", typeof(int)) { IsIndexed = true },
                    new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 4) { IndexKind = this.IndexKind },
                ]
            };

        protected override List<MultiTextStringRecord<TKey>> BuildTestData()
        {
            // All records have the same vector - this fixture is about testing the full text search portion of hybrid search
            var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

            return
            [
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Text1 = "Apples",
                    Text2 = "Oranges",
                    Code = 1,
                    Vector = vector
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Text1 = "Oranges",
                    Text2 = "Apples",
                    Code = 2,
                    Vector = vector
                }
            ];
        }

        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, vectorSize: 4);
    }
}
