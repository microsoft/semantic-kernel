// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Chroma;

public sealed class ChromaMemoryStoreTests : IDisposable
{
    public ChromaMemoryStoreTests()
    {
        this._httpClient = new();
        this._httpClient.BaseAddress = new Uri("http://localhost:8000");

        this._chromaMemoryStore = new(this._httpClient);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanCreateCollectionsAsync()
    {
        // Arrange
        var collectionName1 = "SK" + Guid.NewGuid();
        var collectionName2 = "SK" + Guid.NewGuid();
        var collectionName3 = "SK" + Guid.NewGuid();

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

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanHandleDuplicateNameDuringCollectionCreationAsync()
    {
        // Arrange
        const int expectedCollectionCount = 1;
        var collectionName = "SK" + Guid.NewGuid();

        // Act
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Assert
        var collections = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        var filteredCollections = collections.Where(collection => collection.Equals(collectionName, StringComparison.Ordinal)).ToList();

        Assert.Equal(expectedCollectionCount, filteredCollections.Count);
    }

    [Theory]
    //[Theory(Skip = "Requires Chroma server up and running")]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCheckIfCollectionExistsAsync(bool createCollection)
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

        if (createCollection)
        {
            await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        }

        // Act
        bool doesCollectionExist = await this._chromaMemoryStore.DoesCollectionExistAsync(collectionName);

        // Assert
        Assert.Equal(createCollection, doesCollectionExist);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanDeleteExistingCollectionAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        var collectionsBeforeDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.Contains(collectionName, collectionsBeforeDeletion);

        // Act
        await this._chromaMemoryStore.DeleteCollectionAsync(collectionName);

        // Assert
        var collectionsAfterDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.DoesNotContain(collectionName, collectionsAfterDeletion);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItThrowsExceptionOnNonExistentCollectionDeletionAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

        // Act
        var exception = await Record.ExceptionAsync(() => this._chromaMemoryStore.DeleteCollectionAsync(collectionName));

        // Assert
        Assert.IsType<ChromaMemoryStoreException>(exception);
        Assert.Contains(
            $"Cannot delete non-existent collection {collectionName}",
            exception.Message,
            StringComparison.InvariantCulture);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItReturnsNullOnNonExistentRecordRetrieval()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();
        var key = Guid.NewGuid().ToString();

        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Act
        var record = await this._chromaMemoryStore.GetAsync(collectionName, key, true);

        // Assert
        Assert.Null(record);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanUpsertMemoryRecordAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();
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

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanUpsertMemoryRecordBatchAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

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

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanRemoveMemoryRecordAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();
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

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItCanRemoveMemoryRecordBatchAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();
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

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region private ================================================================================

    private readonly HttpClient _httpClient;
    private readonly ChromaMemoryStore _chromaMemoryStore;

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._httpClient.Dispose();
        }
    }

    private void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Embedding.Vector, actualRecord.Embedding.Vector);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);
    }

    private MemoryRecord GetRandomMemoryRecord()
    {
        var id = Guid.NewGuid().ToString();
        var key = Guid.NewGuid().ToString();
        var embedding = new Embedding<float>(new[] { 1f, 3f, 5f });

        return MemoryRecord.LocalRecord(
            id: id,
            text: "text" + Guid.NewGuid().ToString(),
            description: "description" + Guid.NewGuid().ToString(),
            embedding: embedding,
            additionalMetadata: "custom metadata" + Guid.NewGuid().ToString(),
            key: key);
    }

    #endregion
}
