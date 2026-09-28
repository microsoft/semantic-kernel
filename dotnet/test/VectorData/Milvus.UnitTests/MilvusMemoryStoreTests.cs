// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Milvus;
using Microsoft.SemanticKernel.Memory;
using Milvus.Client;
using Testcontainers.Milvus;
using Xunit;

namespace SemanticKernel.Connectors.Milvus.UnitTests;

[Trait("Category", "MilvusIntegration")]
public sealed class MilvusMemoryStoreTests : IAsyncLifetime
{
    // For manual testing with Docker only. Set to null locally to enable these tests.
    private const string? SkipReason = "For manual testing only; requires Docker.";

    private readonly MilvusFixture _fixture = new();
    private readonly string _collectionName = "id_regression_" + Guid.NewGuid().ToString("N");
    private MilvusMemoryStore _store = null!;

    public static TheoryData<string> UnusualIds => new()
    {
        "ordinary",
        "quotes\"and'single",
        "brackets[],commas",
        "backslash\\and\\\"quote\\",
        "line\r\nbreak\ttab",
        "literal\\r\\n\\t",
        "controls\0\b\f\v\u001f\u007f\u0085",
        "\u00e9\u4e2d\ud83d\ude00",
        "a\"] || true || id in [\"",
        "z\"] && text like \"%secret%\" || id in [\"",
        "x\" || id != \"",
        "a\",\"victim"
    };

    public async Task InitializeAsync()
    {
        await this._fixture.InitializeAsync();
        this._store = new MilvusMemoryStore(
            this._fixture.Container.Hostname,
            port: this._fixture.Container.GetMappedPublicPort(MilvusBuilder.MilvusGrpcPort),
            vectorSize: 2,
            consistencyLevel: ConsistencyLevel.Strong);

        // Create the fixture directly so these tests only depend on the ID operations under test.
        MilvusCollection collection = await this._store.Client.CreateCollectionAsync(
            this._collectionName,
            new CollectionSchema
            {
                Fields =
                {
                    FieldSchema.CreateVarchar("id", maxLength: 1024, isPrimaryKey: true, autoId: false),
                    FieldSchema.CreateFloatVector("embedding", 2)
                },
                EnableDynamicFields = true
            },
            ConsistencyLevel.Strong);
        await collection.CreateIndexAsync("embedding", IndexType.Flat, SimilarityMetricType.Ip);
        await collection.LoadAsync();
        await collection.WaitForCollectionLoadAsync(
            waitingInterval: TimeSpan.FromMilliseconds(100), timeout: TimeSpan.FromMinutes(1));
    }

    public async Task DisposeAsync()
    {
        try
        {
            if (this._store is not null)
            {
                await this._store.DeleteCollectionAsync(this._collectionName);
            }
        }
        finally
        {
            this._store?.Dispose();
            await this._fixture.DisposeAsync();
        }
    }

    [Theory(Skip = SkipReason)]
    [MemberData(nameof(UnusualIds))]
    public async Task ReadsAndDeletesOnlyTheExactIdsAsync(string key)
    {
        MemoryRecord record = CreateRecord(key, [1, 0]);
        MemoryRecord victim = CreateRecord("victim", [0, 1]);
        await this.InsertRecordsAsync(record, victim);

        foreach (bool withEmbeddings in new[] { false, true })
        {
            MemoryRecord? single = await this._store.GetAsync(this._collectionName, key, withEmbeddings);
            AssertRecord(record, single, withEmbeddings);

            List<MemoryRecord> batch = await this._store.GetBatchAsync(this._collectionName, [key], withEmbeddings).ToListAsync();
            AssertRecord(record, Assert.Single(batch), withEmbeddings);
        }

        await this._store.RemoveAsync(this._collectionName, key);
        Assert.Null(await this._store.GetAsync(this._collectionName, key));
        AssertRecord(victim, await this._store.GetAsync(this._collectionName, "victim"), false);

        await this.InsertRecordsAsync(record, CreateRecord("second", [0.5f, 0.5f]));

        List<MemoryRecord> restored = await this._store.GetBatchAsync(
            this._collectionName, [key, "second"], withEmbeddings: true).ToListAsync();
        Assert.Equal(2, restored.Count);
        AssertRecord(record, Assert.Single(restored, item => item.Metadata.Id == key), true);

        await this._store.RemoveBatchAsync(this._collectionName, [key, "second"]);
        Assert.Empty(await this._store.GetBatchAsync(this._collectionName, [key, "second"]).ToListAsync());
        AssertRecord(victim, await this._store.GetAsync(this._collectionName, "victim"), false);
    }

    [Theory(Skip = SkipReason)]
    [MemberData(nameof(UnusualIds))]
    public async Task SearchUsesStoredIdsLiterallyAsync(string key)
    {
        MemoryRecord record = CreateRecord(key, [1, 0]);
        MemoryRecord victim = CreateRecord("victim", [0, 1]);
        await this.InsertRecordsAsync(record, victim);
        await this._store.Client.GetCollection(this._collectionName).FlushAsync();

        foreach (bool withEmbeddings in new[] { false, true })
        {
            List<(MemoryRecord, double)> matches = await this._store.GetNearestMatchesAsync(
                this._collectionName, new float[] { 1, 0 }, limit: 2, withEmbeddings: withEmbeddings).ToListAsync();
            Assert.Equal(2, matches.Count);
            AssertRecord(record, matches[0].Item1, withEmbeddings);
            AssertRecord(victim, matches[1].Item1, withEmbeddings);

            (MemoryRecord, double)? nearest = await this._store.GetNearestMatchAsync(
                this._collectionName, new float[] { 1, 0 }, withEmbedding: withEmbeddings);
            Assert.NotNull(nearest);
            AssertRecord(record, nearest.Value.Item1, withEmbeddings);
        }
    }

    private static MemoryRecord CreateRecord(string key, float[] embedding)
        => MemoryRecord.LocalRecord(key, "text for " + key, description: null, embedding, key: key);

    [Theory(Skip = SkipReason)]
    [InlineData("quotes\"", "quotes\\\"")]
    [InlineData("line\nbreak", "line\\nbreak")]
    [InlineData("slash\\", "slash\\\\")]
    public async Task DoesNotConfuseAnIdWithItsEscapedSpellingAsync(string key, string otherKey)
    {
        MemoryRecord expected = CreateRecord(key, [1, 0]);
        MemoryRecord other = CreateRecord(otherKey, [0, 1]);
        await this.InsertRecordsAsync(expected, other);

        AssertRecord(expected, await this._store.GetAsync(this._collectionName, key), false);
        await this._store.RemoveAsync(this._collectionName, key);
        Assert.Null(await this._store.GetAsync(this._collectionName, key));
        AssertRecord(other, await this._store.GetAsync(this._collectionName, otherKey), false);
    }

    [Fact(Skip = SkipReason)]
    public async Task MissingHostileIdsDoNotReadOrDeleteOtherRecordsAsync()
    {
        MemoryRecord victim = CreateRecord("victim", [1, 0]);
        await this.InsertRecordsAsync(victim);
        string[] keys = ["a\",\"victim", "a\"] || true || id in [\""];

        foreach (string key in keys)
        {
            Assert.Null(await this._store.GetAsync(this._collectionName, key));
            await this._store.RemoveAsync(this._collectionName, key);
        }

        Assert.Empty(await this._store.GetBatchAsync(this._collectionName, keys).ToListAsync());
        await this._store.RemoveBatchAsync(this._collectionName, keys);
        AssertRecord(victim, await this._store.GetAsync(this._collectionName, "victim"), false);
    }

    private async Task InsertRecordsAsync(params MemoryRecord[] records)
    {
        // Seed typed records independently of the legacy client's Upsert response handling.
        FieldData[] fields =
        [
            FieldData.Create("id", records.Select(record => record.Metadata.Id).ToArray()),
            FieldData.CreateFloatVector("embedding", records.Select(record => record.Embedding).ToArray()),
            FieldData.Create("text", records.Select(record => record.Metadata.Text).ToArray(), isDynamic: true),
            FieldData.Create("is_reference", records.Select(record => record.Metadata.IsReference).ToArray(), isDynamic: true),
            FieldData.Create("external_source_name", records.Select(record => record.Metadata.ExternalSourceName).ToArray(), isDynamic: true),
            FieldData.Create("description", records.Select(record => record.Metadata.Description).ToArray(), isDynamic: true),
            FieldData.Create("additional_metadata", records.Select(record => record.Metadata.AdditionalMetadata).ToArray(), isDynamic: true),
            FieldData.Create("key", records.Select(record => record.Key).ToArray(), isDynamic: true),
            FieldData.Create("timestamp", records.Select(_ => string.Empty).ToArray(), isDynamic: true)
        ];
        await this._store.Client.GetCollection(this._collectionName).InsertAsync(fields);
    }

    private static void AssertRecord(MemoryRecord expected, MemoryRecord? actual, bool withEmbedding)
    {
        Assert.NotNull(actual);
        Assert.Equal(expected.Metadata.Id, actual.Metadata.Id);
        Assert.Equal(expected.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(withEmbedding ? expected.Embedding.ToArray() : [], actual.Embedding.ToArray());
    }
}
