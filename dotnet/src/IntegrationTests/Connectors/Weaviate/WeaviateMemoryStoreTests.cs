// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Weaviate;

/// <summary>
/// Tests for <see cref="WeaviateMemoryStore" /> collection and upsert operations.
/// These tests can be run by launching a Weaviate instance using the docker-compose.yml file found in this directory.
/// The Weaviate instance API key is set in the Docker Container as "my-secret-key".
/// </summary>
[Collection("Sequential")]
public class WeaviateMemoryStoreTests
{
    private static readonly HttpClient s_httpClient = new();
    private static readonly WeaviateMemoryStore s_weaviateMemoryStore = new("http", "localhost", 8080, "my-secret-key", httpClient: s_httpClient);

    [Fact(Skip = "Do not run on CI")]
    public async Task EnsureConflictingCollectionNamesAreHandledForCreateAsync()
    {
        var collectionName = "SK" + Guid.NewGuid();

        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));

        var conflictingCollectionName = $"___{collectionName}";
        await Assert.ThrowsAsync<WeaviateMemoryException>(async () =>
            await s_weaviateMemoryStore.CreateCollectionAsync(conflictingCollectionName));
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task EnsureConflictingCollectionNamesAreHandledForDoesExistAsync()
    {
        var collectionName = "SK" + Guid.NewGuid();

        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));

        var conflictingCollectionName = $"___{collectionName}";
        await Assert.ThrowsAsync<WeaviateMemoryException>(async () =>
            await s_weaviateMemoryStore.DoesCollectionExistAsync(conflictingCollectionName));
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task EnsureConflictingCollectionNamesAreHandledForDeleteAsync()
    {
        var collectionName = "SK" + Guid.NewGuid();

        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));

        var conflictingCollectionName = $"___{collectionName}";
        await Assert.ThrowsAsync<WeaviateMemoryException>(async () =>
            await s_weaviateMemoryStore.DeleteCollectionAsync(conflictingCollectionName));
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task ItCreatesNewCollectionAsync()
    {
        var collectionName = "SK" + Guid.NewGuid();
        Assert.False(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));
        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task ItListsCollectionsAsync()
    {
        await DeleteAllClassesAsync();

        Assert.Empty(await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync());

        var collectionName = "SK" + Guid.NewGuid();
        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));

        Assert.Single((await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync()));

        var collectionName2 = "SK" + Guid.NewGuid();
        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName2);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName2));

        Assert.Equal(2, (await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync()).Count);
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task ItDeletesCollectionAsync()
    {
        await DeleteAllClassesAsync();

        Assert.Empty((await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync()));

        var collectionName = "SK" + Guid.NewGuid();
        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        Assert.True(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));

        Assert.Single((await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync()));

        await s_weaviateMemoryStore.DeleteCollectionAsync(collectionName);
        Assert.False(await s_weaviateMemoryStore.DoesCollectionExistAsync(collectionName));
        Assert.Empty((await s_weaviateMemoryStore.GetCollectionsAsync().ToListAsync()));
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task CrudOperationsAsync()
    {
        var id = Guid.NewGuid().ToString();
        var collectionName = "SK" + Guid.NewGuid();
        var timestamp = new DateTimeOffset(2023, 1, 1, 1, 1, 1, new(0));
        var embedding = new Embedding<float>(new[] { 1f, 1f, 1f });

        var memoryRecord = MemoryRecord.LocalRecord(
            id: id,
            text: "this is the text",
            description: "this is the description",
            embedding: embedding,
            additionalMetadata: "custom metadata",
            key: "existing+" + id,
            timestamp: timestamp);

        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        var responseId = await s_weaviateMemoryStore.UpsertAsync(collectionName, memoryRecord);
        Assert.Equal(id, responseId);

        var memoryRecordResultNoVector = await s_weaviateMemoryStore.GetAsync(collectionName, id);
        if (memoryRecordResultNoVector == null)
        {
            Assert.Fail("Unable to retrieve record");
        }

        Assert.Equal(id, memoryRecordResultNoVector.Key);
        Assert.Equal(timestamp, memoryRecordResultNoVector.Timestamp);
        Assert.Equal(Array.Empty<float>(), memoryRecordResultNoVector.Embedding.Vector);
        Assert.True(memoryRecordResultNoVector.HasTimestamp);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Id, memoryRecordResultNoVector.Metadata.Id);
        Assert.Equal(memoryRecordResultNoVector.Metadata.AdditionalMetadata, memoryRecordResultNoVector.Metadata.AdditionalMetadata);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Text, memoryRecordResultNoVector.Metadata.Text);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Description, memoryRecordResultNoVector.Metadata.Description);
        Assert.Equal(memoryRecordResultNoVector.Metadata.ExternalSourceName, memoryRecordResultNoVector.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecordResultNoVector.Metadata.IsReference, memoryRecordResultNoVector.Metadata.IsReference);

        var memoryRecordResultWithVector = await s_weaviateMemoryStore.GetAsync(collectionName, id, true);
        if (memoryRecordResultWithVector == null)
        {
            Assert.Fail("Unable to retrieve record");
        }

        Assert.Equal(id, memoryRecordResultWithVector.Key);
        Assert.Equal(timestamp, memoryRecordResultWithVector.Timestamp);
        Assert.Equal(memoryRecord.Embedding.Vector, memoryRecordResultWithVector.Embedding.Vector);
        Assert.True(memoryRecordResultWithVector.HasTimestamp);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Id, memoryRecordResultWithVector.Metadata.Id);
        Assert.Equal(memoryRecordResultNoVector.Metadata.AdditionalMetadata, memoryRecordResultWithVector.Metadata.AdditionalMetadata);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Text, memoryRecordResultWithVector.Metadata.Text);
        Assert.Equal(memoryRecordResultNoVector.Metadata.Description, memoryRecordResultWithVector.Metadata.Description);
        Assert.Equal(memoryRecordResultNoVector.Metadata.ExternalSourceName, memoryRecordResultWithVector.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecordResultNoVector.Metadata.IsReference, memoryRecordResultWithVector.Metadata.IsReference);

        await s_weaviateMemoryStore.RemoveAsync(collectionName, id);
        var memoryRecordAfterDeletion = await s_weaviateMemoryStore.GetAsync(collectionName, id);
        if (memoryRecordAfterDeletion != null)
        {
            Assert.Fail("Unable to delete record");
        }
    }

    [Fact(Skip = "Do not run on CI")]
    public async Task BatchCrudOperationsAsync()
    {
        var collectionName = "SK" + Guid.NewGuid();

        var id1 = Guid.NewGuid().ToString();
        var timestamp1 = new DateTimeOffset(2023, 1, 1, 1, 1, 1, new(0));
        var embedding1 = new Embedding<float>(new[] { 1f, 1f, 1f });

        var id2 = Guid.NewGuid().ToString();
        var timestamp2 = new DateTimeOffset(2023, 1, 1, 1, 1, 1, new(0));
        var embedding2 = new Embedding<float>(new[] { 2f, 2f, 2f });

        var id3 = Guid.NewGuid().ToString();
        var timestamp3 = new DateTimeOffset(2023, 1, 1, 1, 1, 1, new(0));
        var embedding3 = new Embedding<float>(new[] { 3f, 3f, 3f });

        var memoryRecord1 = MemoryRecord.LocalRecord(
            id: id1,
            text: "this is the text 1",
            description: "this is the description 1",
            embedding: embedding1,
            additionalMetadata: "custom metadata 1",
            key: "existing1+" + id1,
            timestamp: timestamp1);

        var memoryRecord2 = MemoryRecord.LocalRecord(
            id: id2,
            text: "this is the text 2",
            description: "this is the description 2",
            embedding: embedding2,
            additionalMetadata: "custom metadata 2",
            key: "existing2+" + id2,
            timestamp: timestamp2);

        var memoryRecord3 = MemoryRecord.LocalRecord(
            id: id3,
            text: "this is the text 3",
            description: "this is the description 3",
            embedding: embedding3,
            additionalMetadata: "custom metadata 3",
            key: "existing3+" + id3,
            timestamp: timestamp3);

        await s_weaviateMemoryStore.CreateCollectionAsync(collectionName);
        var response = await s_weaviateMemoryStore.UpsertBatchAsync(collectionName, new[] { memoryRecord1, memoryRecord2, memoryRecord3 }).ToListAsync();
        Assert.Equal(id1, response[0]);
        Assert.Equal(id2, response[1]);
        Assert.Equal(id3, response[2]);

        var results = await s_weaviateMemoryStore.GetNearestMatchesAsync(collectionName, embedding1, 100, 0.8, true).ToListAsync();

        (MemoryRecord, double) first = results[0];
        (MemoryRecord, double) second = results[1];

        Assert.Equal(id3, first.Item1.Key);
        Assert.Equal(memoryRecord3.Timestamp, first.Item1.Timestamp);
        Assert.Equal(memoryRecord3.Embedding.Vector, first.Item1.Embedding.Vector);
        Assert.True(first.Item1.HasTimestamp);
        Assert.Equal(memoryRecord3.Metadata.Id, first.Item1.Metadata.Id);
        Assert.Equal(memoryRecord3.Metadata.AdditionalMetadata, first.Item1.Metadata.AdditionalMetadata);
        Assert.Equal(memoryRecord3.Metadata.Text, first.Item1.Metadata.Text);
        Assert.Equal(memoryRecord3.Metadata.Description, first.Item1.Metadata.Description);
        Assert.Equal(memoryRecord3.Metadata.ExternalSourceName, first.Item1.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecord3.Metadata.IsReference, first.Item1.Metadata.IsReference);

        Assert.Equal(id2, second.Item1.Key);
        Assert.Equal(memoryRecord2.Timestamp, second.Item1.Timestamp);
        Assert.Equal(memoryRecord2.Embedding.Vector, second.Item1.Embedding.Vector);
        Assert.True(second.Item1.HasTimestamp);
        Assert.Equal(memoryRecord2.Metadata.Id, second.Item1.Metadata.Id);
        Assert.Equal(memoryRecord2.Metadata.AdditionalMetadata, second.Item1.Metadata.AdditionalMetadata);
        Assert.Equal(memoryRecord2.Metadata.Text, second.Item1.Metadata.Text);
        Assert.Equal(memoryRecord2.Metadata.Description, second.Item1.Metadata.Description);
        Assert.Equal(memoryRecord2.Metadata.ExternalSourceName, second.Item1.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecord2.Metadata.IsReference, second.Item1.Metadata.IsReference);

        var closest = await s_weaviateMemoryStore.GetNearestMatchAsync(collectionName, embedding1, 0.8, true);
        Assert.Equal(id3, closest!.Value.Item1.Key);
        Assert.Equal(memoryRecord3.Timestamp, closest.Value.Item1.Timestamp);
        Assert.Equal(memoryRecord3.Embedding.Vector, closest.Value.Item1.Embedding.Vector);
        Assert.True(closest.Value.Item1.HasTimestamp);
        Assert.Equal(memoryRecord3.Metadata.Id, closest.Value.Item1.Metadata.Id);
        Assert.Equal(memoryRecord3.Metadata.AdditionalMetadata, closest.Value.Item1.Metadata.AdditionalMetadata);
        Assert.Equal(memoryRecord3.Metadata.Text, closest.Value.Item1.Metadata.Text);
        Assert.Equal(memoryRecord3.Metadata.Description, closest.Value.Item1.Metadata.Description);
        Assert.Equal(memoryRecord3.Metadata.ExternalSourceName, closest.Value.Item1.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecord3.Metadata.IsReference, closest.Value.Item1.Metadata.IsReference);

        await s_weaviateMemoryStore.RemoveBatchAsync(collectionName, new[] { id1, id2, id3 });
        var memoryRecordsAfterDeletion = await s_weaviateMemoryStore.GetBatchAsync(collectionName, new[] { id1, id2, id3 }).ToListAsync();
        Assert.Empty(memoryRecordsAfterDeletion);
    }

    private static async Task DeleteAllClassesAsync()
    {
        var classes = s_weaviateMemoryStore.GetCollectionsAsync();
        await foreach (var @class in classes)
        {
#pragma warning disable CA2000
            await s_httpClient.SendAsync(new(HttpMethod.Delete, $"schema/{@class}"));
#pragma warning restore CA2000
        }
    }
}
