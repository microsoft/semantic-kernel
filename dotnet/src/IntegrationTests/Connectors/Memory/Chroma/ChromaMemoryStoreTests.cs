// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;
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
    public async Task ItCreatesCollectionsAsync()
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
        var collectionName = "SK" + Guid.NewGuid();

        // Act
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);

        // Assert
        var collections = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        var filteredCollections = collections.Where(collection => collection.Equals(collectionName, StringComparison.Ordinal)).ToList();

        Assert.Equal(1, filteredCollections.Count);
    }

    [Theory]
    //[Theory(Skip = "Requires Chroma server up and running")]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCheckIfCollectionExistsAsync(bool createCollection)
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

        // Act
        if (createCollection)
        {
            await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        }

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

        // Act
        await this._chromaMemoryStore.CreateCollectionAsync(collectionName);
        var collectionsBeforeDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.Contains(collectionName, collectionsBeforeDeletion);

        await this._chromaMemoryStore.DeleteCollectionAsync(collectionName);

        // Assert
        var collectionsAfterDeletion = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.DoesNotContain(collectionName, collectionsAfterDeletion);
    }

    [Fact]
    //[Fact(Skip = "Requires Chroma server up and running")]
    public async Task ItThrowsExceptionOnNonExistingCollectionDeletionAsync()
    {
        // Arrange
        var collectionName = "SK" + Guid.NewGuid();

        // Act
        var collections = await this._chromaMemoryStore.GetCollectionsAsync().ToListAsync();
        Assert.DoesNotContain(collectionName, collections);

        var exception = await Record.ExceptionAsync(() => this._chromaMemoryStore.DeleteCollectionAsync(collectionName));

        // Assert
        Assert.IsType<ChromaMemoryStoreException>(exception);
        Assert.Contains(
            $"Cannot delete non existing collection {collectionName}",
            exception.Message,
            StringComparison.InvariantCulture);
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

    #endregion
}
