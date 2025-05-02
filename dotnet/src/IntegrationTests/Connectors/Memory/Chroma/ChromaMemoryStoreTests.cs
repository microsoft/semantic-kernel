// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Chroma;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Chroma;

/// <summary>
/// Integration tests for <see cref="ChromaMemoryStore"/> class.
/// Tests work with local Chroma server. To setup the server, see dotnet/src/Connectors/Connectors.Memory.Chroma/README.md.
/// </summary>
[Experimental("SKEXP0020")]
public sealed class ChromaMemoryStoreTests : IDisposable
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Chroma server up and running";

    private const string BaseAddress = "http://localhost:8000";

    public ChromaMemoryStoreTests()
    {
        this._httpClient = new()
        {
            BaseAddress = new Uri(BaseAddress)
        };

        this._chromaMemoryStore = new(this._httpClient);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionsAsync()
    {
        // Arrange
        var collectionName1 = this.GetRandomCollectionName();
        var collectionName2 = this.GetRandomCollectionName();
        var collectionName3 = this.GetRandomCollectionName();

        // Act
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName1);
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName2);
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName3);

        // Assert
        var collections = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();

        Assert.Contains(collectionName1, collections);
        Assert.Contains(collectionName2, collections);
        Assert.Contains(collectionName3, collections);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanHandleDuplicateNameDuringCollectionCreationAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        // Act
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Assert
        var collections = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        var filteredCollections = collections.Where(collection => collection.Equals(collectionName, StringComparison.Ordinal)).ToList();

        Assert.Single(filteredCollections);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCheckIfCollectionExistsAsync(bool createCollection)
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        if (createCollection)
        {
            await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        }

        // Act
        bool doesCollectionExist = await this._chromaMemoryStore.DoesCollectionExistAsync(collectionName);

        // Assert
        Assert.Equal(createCollection, doesCollectionExist);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteExistingCollectionAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        var collectionsBeforeDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.Contains(collectionName, collectionsBeforeDeletion);

        // Act
        await this._chromaMemoryStore.DeleteCollectionAsync(collectionName);

        // Assert
        var collectionsAfterDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.DoesNotContain(collectionName, collectionsAfterDeletion);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsExceptionOnNonExistentCollectionDeletionAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        // Act
        var exception = await Record.ExceptionAsync(() => this._chromaMemoryStore.DeleteCollectionAsync(collectionName));

        // Assert
        Assert.IsType<KernelException>(exception);
        Assert.Contains(
            $"Cannot delete non-existent collection {collectionName}",
            exception.Message,
            StringComparison.InvariantCulture);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNullOnNonExistentRecordRetrievalAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var key = Guid.NewGuid().ToString();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var record = await this._chromaMemoryStore.GetAsync(collectionName, key, true);

        // Assert
        Assert.Null(record);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertMemoryRecordAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var expectedRecord = this.GetRandomMemoryRecord();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var createdRecordKey = await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);

        // Assert
        Assert.Equal(expectedRecord.Key, createdRecordKey);

        var actualRecord = await this._chromaMemoryStore.GetAsync(collectionName, expectedRecord.Key, true);

        Assert.NotNull(actualRecord);

        this.AssertMemoryRecordEqual(expectedRecord, actualRecord);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertMemoryRecordBatchAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        var expectedRecord1 = this.GetRandomMemoryRecord();
        var expectedRecord2 = this.GetRandomMemoryRecord();
        var expectedRecord3 = this.GetRandomMemoryRecord();

        var batch = new List<MemoryRecord> { expectedRecord1, expectedRecord2, expectedRecord3 };

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var createdRecordKeys = await this._chromaMemoryStore.UpsertBatchAsync(collectionName, batch).ToListAsync();

        // Assert
        Assert.Equal(expectedRecord1.Key, createdRecordKeys[0]);
        Assert.Equal(expectedRecord2.Key, createdRecordKeys[1]);
        Assert.Equal(expectedRecord3.Key, createdRecordKeys[2]);

        var actualRecords = await this._chromaMemoryStore.GetBatchAsync(collectionName, batch.Select(l => l.Key), true).ToListAsync();

        actualRecords.ForEach(Assert.NotNull);

        this.AssertMemoryRecordEqual(expectedRecord1, actualRecords[0]);
        this.AssertMemoryRecordEqual(expectedRecord2, actualRecords[1]);
        this.AssertMemoryRecordEqual(expectedRecord3, actualRecords[2]);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveMemoryRecordAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var expectedRecord = this.GetRandomMemoryRecord();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);

        var recordBeforeDeletion = await this._chromaMemoryStore.GetAsync(collectionName, expectedRecord.Key);
        Assert.NotNull(recordBeforeDeletion);

        // Act
        await this._chromaMemoryStore.RemoveAsync(collectionName, expectedRecord.Key);

        // Assert
        var recordAfterDeletion = await this._chromaMemoryStore.GetAsync(collectionName, expectedRecord.Key);
        Assert.Null(recordAfterDeletion);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveMemoryRecordBatchAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        var expectedRecord1 = this.GetRandomMemoryRecord();
        var expectedRecord2 = this.GetRandomMemoryRecord();
        var expectedRecord3 = this.GetRandomMemoryRecord();

        var batch = new List<MemoryRecord> { expectedRecord1, expectedRecord2, expectedRecord3 };
        var keys = batch.Select(l => l.Key);

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.UpsertBatchAsync(collectionName, batch).ToListAsync();

        var recordsBeforeDeletion = await this._chromaMemoryStore.GetBatchAsync(collectionName, keys).ToListAsync();

        Assert.Equal(batch.Count, recordsBeforeDeletion.Count);
        recordsBeforeDeletion.ForEach(Assert.NotNull);

        // Act
        await this._chromaMemoryStore.RemoveBatchAsync(collectionName, keys);

        // Assert
        var recordsAfterDeletion = await this._chromaMemoryStore.GetBatchAsync(collectionName, keys).ToListAsync();
        Assert.Empty(recordsAfterDeletion);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetNearestMatchAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        var expectedRecord1 = this.GetRandomMemoryRecord(embedding: new[] { 10f, 10f, 10f });
        var expectedRecord2 = this.GetRandomMemoryRecord(embedding: new[] { 5f, 5f, 5f });
        var expectedRecord3 = this.GetRandomMemoryRecord(embedding: new[] { 1f, 1f, 1f });

        float[] searchEmbedding = [2f, 2f, 2f];

        var batch = new List<MemoryRecord> { expectedRecord1, expectedRecord2, expectedRecord3 };
        var keys = batch.Select(l => l.Key);

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.UpsertBatchAsync(collectionName, batch).ToListAsync();

        // Act
        var nearestMatch = await this._chromaMemoryStore.GetNearestMatchAsync(collectionName, searchEmbedding, withEmbedding: true);

        // Assert
        Assert.True(nearestMatch.HasValue);

        var actualRecord = nearestMatch.Value.Item1;

        Assert.NotNull(actualRecord);

        this.AssertMemoryRecordEqual(expectedRecord3, actualRecord);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetNearestMatchesAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();

        var expectedRecord1 = this.GetRandomMemoryRecord(embedding: new[] { 10f, 10f, 10f });
        var expectedRecord2 = this.GetRandomMemoryRecord(embedding: new[] { 5f, 5f, 5f });
        var expectedRecord3 = this.GetRandomMemoryRecord(embedding: new[] { 1f, 1f, 1f });

        float[] searchEmbedding = [2f, 2f, 2f];

        var batch = new List<MemoryRecord> { expectedRecord1, expectedRecord2, expectedRecord3 };
        var keys = batch.Select(l => l.Key);

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.UpsertBatchAsync(collectionName, batch).ToListAsync();

        // Act
        var nearestMatches = await this._chromaMemoryStore
            .GetNearestMatchesAsync(collectionName, searchEmbedding, batch.Count, withEmbeddings: true)
            .ToListAsync();

        // Assert
        Assert.NotNull(nearestMatches);
        Assert.Equal(batch.Count, nearestMatches.Count);

        nearestMatches.ForEach(match => Assert.NotNull(match.Item1));

        var actualRecord1 = nearestMatches[0].Item1;
        var actualRecord2 = nearestMatches[1].Item1;
        var actualRecord3 = nearestMatches[2].Item1;

        this.AssertMemoryRecordEqual(expectedRecord3, actualRecord1);
        this.AssertMemoryRecordEqual(expectedRecord2, actualRecord2);
        this.AssertMemoryRecordEqual(expectedRecord1, actualRecord3);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNoMatchesFromEmptyCollectionAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        float[] searchEmbedding = [2f, 2f, 2f];

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var nearestMatch = await this._chromaMemoryStore.GetNearestMatchAsync(collectionName, searchEmbedding, withEmbedding: true);

        // Assert
        Assert.Null(nearestMatch?.Item1);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertSameMemoryRecordMultipleTimesAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var expectedRecord = this.GetRandomMemoryRecord();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);

        // Assert
        var actualRecord = await this._chromaMemoryStore.GetAsync(collectionName, expectedRecord.Key, true);

        Assert.NotNull(actualRecord);

        this.AssertMemoryRecordEqual(expectedRecord, actualRecord);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertDifferentMemoryRecordsWithSameKeyMultipleTimesAsync()
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var expectedRecord1 = this.GetRandomMemoryRecord();
        var key = expectedRecord1.Key;

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord1);

        var actualRecord1 = await this._chromaMemoryStore.GetAsync(collectionName, key, withEmbedding: true);

        Assert.NotNull(actualRecord1);
        this.AssertMemoryRecordEqual(expectedRecord1, actualRecord1);

        // Act
        var expectedRecord2 = this.GetRandomMemoryRecord(key: key);
        await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord2);

        // Assert
        var actualRecord2 = await this._chromaMemoryStore.GetAsync(collectionName, key, withEmbedding: true);

        Assert.NotNull(actualRecord2);
        this.AssertMemoryRecordEqual(expectedRecord2, actualRecord2);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItProcessesBooleanValuesCorrectlyAsync(bool isReference)
    {
        // Arrange
        var collectionName = this.GetRandomCollectionName();
        var metadata = this.GetRandomMemoryRecordMetadata(isReference: isReference);
        var expectedRecord = this.GetRandomMemoryRecord(metadata: metadata);

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var createdRecordKey = await this._chromaMemoryStore.UpsertAsync(collectionName, expectedRecord);
        var actualRecord = await this._chromaMemoryStore.GetAsync(collectionName, createdRecordKey, true);

        // Assert
        Assert.NotNull(actualRecord);

        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    #region private ================================================================================

    private readonly HttpClient _httpClient;
    private readonly ChromaMemoryStore _chromaMemoryStore;

    private void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);
    }

    private string GetRandomCollectionName()
    {
        return "sk-test-" + Guid.NewGuid();
    }

    private MemoryRecord GetRandomMemoryRecord(string? key = null, ReadOnlyMemory<float>? embedding = null)
    {
        var recordKey = key ?? Guid.NewGuid().ToString();
        var recordEmbedding = embedding ?? new[] { 1f, 3f, 5f };

        return MemoryRecord.LocalRecord(
            id: recordKey,
            text: "text-" + Guid.NewGuid().ToString(),
            description: "description-" + Guid.NewGuid().ToString(),
            embedding: recordEmbedding,
            additionalMetadata: "metadata-" + Guid.NewGuid().ToString(),
            key: recordKey);
    }

    private MemoryRecord GetRandomMemoryRecord(MemoryRecordMetadata metadata, ReadOnlyMemory<float>? embedding = null)
    {
        var recordEmbedding = embedding ?? new[] { 1f, 3f, 5f };

        return MemoryRecord.FromMetadata(
            metadata: metadata,
            embedding: recordEmbedding,
            key: metadata.Id);
    }

    private MemoryRecordMetadata GetRandomMemoryRecordMetadata(bool isReference = false, string? key = null)
    {
        var recordKey = key ?? Guid.NewGuid().ToString();

        return new MemoryRecordMetadata(
            isReference: isReference,
            id: recordKey,
            text: "text-" + Guid.NewGuid().ToString(),
            description: "description-" + Guid.NewGuid().ToString(),
            externalSourceName: "source-name-" + Guid.NewGuid().ToString(),
            additionalMetadata: "metadata-" + Guid.NewGuid().ToString());
    }

    #endregion
}
