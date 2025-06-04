// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Milvus;
using Microsoft.SemanticKernel.Memory;
using Milvus.Client;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Milvus;

[Experimental("SKEXP0020")]
public class MilvusMemoryStoreTests(MilvusFixture milvusFixture) : IClassFixture<MilvusFixture>, IAsyncLifetime
{
    private const string CollectionName = "test";

    private readonly MilvusFixture _milvusFixture = milvusFixture;
    private MilvusMemoryStore Store { get; set; } = null!;

    [Fact]
    public async Task CreateCollectionAsync()
    {
        Assert.False(await this.Store.DoesCollectionExistAsync(CollectionName));

        await this.Store.CreateCollectionAsync(CollectionName);
        Assert.True(await this.Store.DoesCollectionExistAsync(CollectionName));
    }

    [Fact]
    public async Task DropCollectionAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.Store.DeleteCollectionAsync(CollectionName);
        Assert.False(await this.Store.DoesCollectionExistAsync(CollectionName));
    }

    [Fact]
    public async Task GetCollectionsAsync()
    {
        await this.Store.CreateCollectionAsync("collection1");
        await this.Store.CreateCollectionAsync("collection2");

        List<string> collections = this.Store.GetCollectionsAsync().ToEnumerable().ToList();
        Assert.Contains("collection1", collections);
        Assert.Contains("collection2", collections);
    }

    [Fact]
    public async Task UpsertAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);

        string id = await this.Store.UpsertAsync(CollectionName, new MemoryRecord(
            new MemoryRecordMetadata(
                isReference: true,
                id: "Some id",
                description: "Some description",
                text: "Some text",
                externalSourceName: "Some external resource name",
                additionalMetadata: "Some additional metadata"),
            new[] { 10f, 11f, 12f, 13f, 14f },
            key: "Some key",
            timestamp: new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero)));

        Assert.Equal("Some id", id);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        MemoryRecord? record = await this.Store.GetAsync(CollectionName, "Some id", withEmbedding: withEmbeddings);
        Assert.NotNull(record);

        Assert.True(record.Metadata.IsReference);
        Assert.Equal("Some id", record.Metadata.Id);
        Assert.Equal("Some description", record.Metadata.Description);
        Assert.Equal("Some text", record.Metadata.Text);
        Assert.Equal("Some external resource name", record.Metadata.ExternalSourceName);
        Assert.Equal("Some additional metadata", record.Metadata.AdditionalMetadata);
        Assert.Equal("Some key", record.Key);
        Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), record.Timestamp);

        Assert.Equal(
            withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
            record.Embedding.ToArray());
    }

    [Fact]
    public async Task UpsertBatchAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        List<string> ids = await this.InsertSampleDataAsync();

        Assert.Collection(ids,
            id => Assert.Equal("Some id", id),
            id => Assert.Equal("Some other id", id));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetBatchAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        List<MemoryRecord> records = this.Store.GetBatchAsync(CollectionName, ["Some id", "Some other id"], withEmbeddings: withEmbeddings).ToEnumerable().ToList();

        Assert.Collection(records.OrderBy(r => r.Metadata.Id),
            r =>
            {
                Assert.True(r.Metadata.IsReference);
                Assert.Equal("Some id", r.Metadata.Id);
                Assert.Equal("Some description", r.Metadata.Description);
                Assert.Equal("Some text", r.Metadata.Text);
                Assert.Equal("Some external resource name", r.Metadata.ExternalSourceName);
                Assert.Equal("Some additional metadata", r.Metadata.AdditionalMetadata);
                Assert.Equal("Some key", r.Key);
                Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
                    r.Embedding.ToArray());
            },
            r =>
            {
                Assert.False(r.Metadata.IsReference);
                Assert.Equal("Some other id", r.Metadata.Id);
                Assert.Empty(r.Metadata.Description);
                Assert.Empty(r.Metadata.Text);
                Assert.Empty(r.Metadata.ExternalSourceName);
                Assert.Empty(r.Metadata.AdditionalMetadata);
                Assert.Empty(r.Key);
                Assert.Null(r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
                    r.Embedding.ToArray());
            });
    }

    [Fact]
    public async Task RemoveAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        using var milvusClient = this._milvusFixture.CreateClient();

        Assert.NotNull(await this.Store.GetAsync(CollectionName, "Some id"));
        await this.Store.RemoveAsync(CollectionName, "Some id");
        Assert.Null(await this.Store.GetAsync(CollectionName, "Some id"));
    }

    [Fact]
    public async Task RemoveBatchAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        Assert.NotNull(await this.Store.GetAsync(CollectionName, "Some id"));
        Assert.NotNull(await this.Store.GetAsync(CollectionName, "Some other id"));
        await this.Store.RemoveBatchAsync(CollectionName, ["Some id", "Some other id"]);
        Assert.Null(await this.Store.GetAsync(CollectionName, "Some id"));
        Assert.Null(await this.Store.GetAsync(CollectionName, "Some other id"));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetNearestMatchesAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        // There seems to be some race condition where the upserted data above isn't taken into account in the search below and zero results are returned...
        await Task.Delay(1000);

        List<(MemoryRecord Record, double SimilarityScore)> results =
            this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, withEmbeddings: withEmbeddings).ToEnumerable().ToList();

        Assert.All(results, t => Assert.True(t.SimilarityScore > 0));

        Assert.Collection(results.OrderBy(r => r.SimilarityScore).Select(r => r.Record),
            r =>
            {
                Assert.True(r.Metadata.IsReference);
                Assert.Equal("Some id", r.Metadata.Id);
                Assert.Equal("Some description", r.Metadata.Description);
                Assert.Equal("Some text", r.Metadata.Text);
                Assert.Equal("Some external resource name", r.Metadata.ExternalSourceName);
                Assert.Equal("Some additional metadata", r.Metadata.AdditionalMetadata);
                Assert.Equal("Some key", r.Key);
                Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
                    r.Embedding.ToArray());
            },
            r =>
            {
                Assert.False(r.Metadata.IsReference);
                Assert.Equal("Some other id", r.Metadata.Id);
                Assert.Empty(r.Metadata.Description);
                Assert.Empty(r.Metadata.Text);
                Assert.Empty(r.Metadata.ExternalSourceName);
                Assert.Empty(r.Metadata.AdditionalMetadata);
                Assert.Empty(r.Key);
                Assert.Null(r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
                    r.Embedding.ToArray());
            });
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetNearestMatchesWithMetricTypeAsync(bool withEmbeddings)
    {
        //Create collection with default, Ip metric
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();
        await this.Store.Client.FlushAsync([CollectionName]);

        //Search with Ip metric, run correctly
        List<(MemoryRecord Record, double SimilarityScore)> ipResults =
            this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, withEmbeddings: withEmbeddings).ToEnumerable().ToList();

        Assert.All(ipResults, t => Assert.True(t.SimilarityScore > 0));

        //Set the store to Cosine metric, without recreate collection
        this.Store = new(this._milvusFixture.Host, vectorSize: 5, port: this._milvusFixture.Port, metricType: SimilarityMetricType.Cosine, consistencyLevel: ConsistencyLevel.Strong);

        //An exception will be thrown here, the exception message includes "metric type not match"
        MilvusException milvusException = Assert.Throws<MilvusException>(() => this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, withEmbeddings: withEmbeddings).ToEnumerable().ToList());

        Assert.NotNull(milvusException);

        Assert.Contains("metric type not match", milvusException.Message);

        //Recreate collection with Cosine metric
        await this.Store.DeleteCollectionAsync(CollectionName);
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();
        await this.Store.Client.FlushAsync([CollectionName]);

        //Search with Ip metric, run correctly
        List<(MemoryRecord Record, double SimilarityScore)> cosineResults =
            this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, withEmbeddings: withEmbeddings).ToEnumerable().ToList();

        Assert.All(cosineResults, t => Assert.True(t.SimilarityScore > 0));
    }

    [Fact]
    public async Task GetNearestMatchesWithMinRelevanceScoreAsync()
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        List<(MemoryRecord Record, double SimilarityScore)> results =
            this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2).ToEnumerable().ToList();

        string firstId = results[0].Record.Metadata.Id;
        double firstSimilarityScore = results[0].SimilarityScore;

        results = this.Store.GetNearestMatchesAsync(CollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, minRelevanceScore: firstSimilarityScore + 0.0001).ToEnumerable().ToList();

        Assert.DoesNotContain(firstId, results.Select(r => r.Record.Metadata.Id));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetNearestMatchAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(CollectionName);
        await this.InsertSampleDataAsync();

        (MemoryRecord Record, double SimilarityScore)? result =
            await this.Store.GetNearestMatchAsync(CollectionName, new[] { 20f, 21f, 22f, 23f, 24f }, withEmbedding: withEmbeddings);

        Assert.NotNull(result);
        Assert.True(result.Value.SimilarityScore > 0);
        MemoryRecord record = result.Value.Record;

        Assert.Equal("Some other id", record.Metadata.Id);
        Assert.Equal(
            withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
            record.Embedding.ToArray());
    }

    private async Task<List<string>> InsertSampleDataAsync()
    {
        IAsyncEnumerable<string> ids = this.Store.UpsertBatchAsync(CollectionName,
        [
            new MemoryRecord(
                new MemoryRecordMetadata(
                    isReference: true,
                    id: "Some id",
                    description: "Some description",
                    text: "Some text",
                    externalSourceName: "Some external resource name",
                    additionalMetadata: "Some additional metadata"),
                new[] { 10f, 11f, 12f, 13f, 14f },
                key: "Some key",
                timestamp: new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero)),
            new MemoryRecord(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: "Some other id",
                    description: "",
                    text: "",
                    externalSourceName: "",
                    additionalMetadata: ""),
                new[] { 20f, 21f, 22f, 23f, 24f },
                key: null,
                timestamp: null),
        ]);

        List<string> idList = [];

        await foreach (string id in ids)
        {
            idList.Add(id);
        }

        return idList;
    }

    public async Task InitializeAsync()
    {
        this.Store = new(this._milvusFixture.Host, vectorSize: 5, port: this._milvusFixture.Port, consistencyLevel: ConsistencyLevel.Strong);
        await this.Store.DeleteCollectionAsync(CollectionName);
    }

    public Task DisposeAsync()
    {
        this.Store.Dispose();
        return Task.CompletedTask;
    }
}
