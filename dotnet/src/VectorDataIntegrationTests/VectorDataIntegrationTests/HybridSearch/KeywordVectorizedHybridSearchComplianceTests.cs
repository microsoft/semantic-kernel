// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.HybridSearch;

/// <summary>
/// Base class for common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
/// <typeparam name="TKey">The type of key to use with the record collection.</typeparam>
public abstract class KeywordVectorizedHybridSearchComplianceTests<TKey>(
    KeywordVectorizedHybridSearchComplianceTests<TKey>.VectorAndStringFixture vectorAndStringFixture,
    KeywordVectorizedHybridSearchComplianceTests<TKey>.MultiTextFixture multiTextFixture)
    where TKey : notnull
{
    protected virtual int DelayAfterIndexCreateInMilliseconds { get; } = 0;

    [ConditionalFact]
    public async Task SearchShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var hybridSearch = vectorAndStringFixture.Collection as IKeywordHybridSearch<VectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the third contains Grapes, so searching for
        // Grapes should return the third record first.
        var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Grapes"]);

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Equal(3, results.Count);

        Assert.Equal(3, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task SearchWithFilterShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var hybridSearch = vectorAndStringFixture.Collection as IKeywordHybridSearch<VectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the second contains Oranges, however
        // adding the filter should limit the results to only the first.
#pragma warning disable CS0618 // Type or member is obsolete
        var options = new HybridSearchOptions<VectorAndStringRecord<TKey>>
        {
            OldFilter = new VectorSearchFilter().EqualTo("Code", 1)
        };
#pragma warning restore CS0618 // Type or member is obsolete
        var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], options);

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(1, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task SearchWithTopShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var hybridSearch = vectorAndStringFixture.Collection as IKeywordHybridSearch<VectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the second contains Oranges, so the
        // second should be returned first.
        var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], new() { Top = 1 });

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(2, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task SearchWithSkipShouldReturnExpectedResultsAsync()
    {
        // Arrange
        var hybridSearch = vectorAndStringFixture.Collection as IKeywordHybridSearch<VectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        // All records have the same vector, but the first and third contain healthy,
        // so when skipping the first two results, we should get the second record.
        var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["healthy"], new() { Skip = 2 });

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Single(results);

        Assert.Equal(2, results[0].Record.Code);
    }

    [ConditionalFact]
    public async Task SearchWithMultipleKeywordsShouldRankMatchedKeywordsHigherAsync()
    {
        // Arrange
        var hybridSearch = vectorAndStringFixture.Collection as IKeywordHybridSearch<VectorAndStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        var searchResult = await hybridSearch!.HybridSearchAsync(vector, ["tangy", "nourishing"]);

        // Assert
        var results = await searchResult.Results.ToListAsync();
        Assert.Equal(3, results.Count);

        Assert.True(results[0].Record.Code.Equals(1) || results[0].Record.Code.Equals(2));
        Assert.True(results[1].Record.Code.Equals(1) || results[1].Record.Code.Equals(2));
        Assert.Equal(3, results[2].Record.Code);
    }

    [ConditionalFact]
    public async Task SearchWithMultiTextRecordSearchesRequestedFieldAsync()
    {
        // Arrange
        var hybridSearch = multiTextFixture.Collection as IKeywordHybridSearch<MultiTextStringRecord<TKey>>;

        var vector = new ReadOnlyMemory<float>([1, 0, 0, 0]);

        // Act
        var searchResult1 = await hybridSearch!.HybridSearchAsync(vector, ["Apples"], new() { AdditionalProperty = r => r.Text2 });
        var searchResult2 = await hybridSearch!.HybridSearchAsync(vector, ["Oranges"], new() { AdditionalProperty = r => r.Text2 });

        // Assert
        var results1 = await searchResult1.Results.ToListAsync();
        Assert.Equal(2, results1.Count);

        Assert.Equal(2, results1[0].Record.Code);
        Assert.Equal(1, results1[1].Record.Code);

        var results2 = await searchResult2.Results.ToListAsync();
        Assert.Equal(2, results2.Count);

        Assert.Equal(1, results2[0].Record.Code);
        Assert.Equal(2, results2[1].Record.Code);
    }

    public sealed class VectorAndStringRecord<TRecordKey>
    {
        public TRecordKey Key { get; set; } = default!;

        public string Text { get; set; } = string.Empty;

        public int Code { get; set; }

        public ReadOnlyMemory<float> Vector { get; set; }
    }

    public sealed class MultiTextStringRecord<TRecordKey>
    {
        public TRecordKey Key { get; set; } = default!;

        public string Text1 { get; set; } = string.Empty;

        public string Text2 { get; set; } = string.Empty;

        public int Code { get; set; }

        public ReadOnlyMemory<float> Vector { get; set; }
    }

    public abstract class VectorAndStringFixture : VectorStoreCollectionFixture<TKey, VectorAndStringRecord<TKey>>
    {
        protected override string CollectionName => "KeywordHybridSearch" + this.GetUniqueCollectionName();

        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = new List<VectorStoreRecordProperty>()
                {
                    new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                    new VectorStoreRecordDataProperty("Text", typeof(string)) { IsFullTextSearchable = true },
                    new VectorStoreRecordDataProperty("Code", typeof(int)) { IsFilterable = true },
                    new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = this.IndexKind },
                }
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

        // In some databases (Azure AI Search), the data shows up but the filtering index isn't yet updated,
        // so filtered searches show empty results. Add a filter to the seed data check below.
        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, vectorSize: 4);
    }

    public abstract class MultiTextFixture : VectorStoreCollectionFixture<TKey, MultiTextStringRecord<TKey>>
    {
        protected override string CollectionName => "KeywordHybridSearch" + this.GetUniqueCollectionName();

        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = new List<VectorStoreRecordProperty>()
                {
                    new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                    new VectorStoreRecordDataProperty("Text1", typeof(string)) { IsFullTextSearchable = true },
                    new VectorStoreRecordDataProperty("Text2", typeof(string)) { IsFullTextSearchable = true },
                    new VectorStoreRecordDataProperty("Code", typeof(int)) { IsFilterable = true },
                    new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = this.IndexKind },
                }
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

        // In some databases (Azure AI Search), the data shows up but the filtering index isn't yet updated,
        // so filtered searches show empty results. Add a filter to the seed data check below.
        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, vectorSize: 4);
    }
}
