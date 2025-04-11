// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Class to store and retrieve text-based memories to and from a vector store.
/// </summary>
/// <typeparam name="TKey">The key type to use with the vector store.</typeparam>
public class VectorDataTextMemoryStore<TKey> : TextMemoryStore, IDisposable
    where TKey : notnull
{
    private readonly IVectorStore _vectorStore;
    private readonly ITextEmbeddingGenerationService _textEmbeddingGenerationService;
    private readonly string _storageNamespace;
    private readonly int _vectorDimensions;
    private readonly Lazy<IVectorStoreRecordCollection<TKey, MemoryDocument<TKey>>> _vectorStoreRecordCollection;
    private readonly SemaphoreSlim _collectionInitializationLock = new(1, 1);
    private bool _collectionInitialized = false;
    private bool _disposedValue;

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorDataTextMemoryStore{TKey}"/> class.
    /// </summary>
    /// <param name="vectorStore">The vector store to store and read the memories from.</param>
    /// <param name="textEmbeddingGenerationService">The service to use for generating embeddings for the memories.</param>
    /// <param name="collectionName">The name of the collection in the vector store to store and read the memories from.</param>
    /// <param name="storageNamespace">The namespace to scope memories to within the collection.</param>
    /// <param name="vectorDimensions">The number of dimentions to use for the memory embeddings.</param>
    /// <exception cref="NotSupportedException">Thrown if the key type provided is not supported.</exception>
    public VectorDataTextMemoryStore(IVectorStore vectorStore, ITextEmbeddingGenerationService textEmbeddingGenerationService, string collectionName, string storageNamespace, int vectorDimensions)
    {
        Verify.NotNull(vectorStore);
        Verify.NotNull(textEmbeddingGenerationService);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(storageNamespace);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(Guid))
        {
            throw new NotSupportedException($"Unsupported key of type '{typeof(TKey).Name}'");
        }

        VectorStoreRecordDefinition memoryDocumentDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>()
            {
                new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                new VectorStoreRecordDataProperty("Namespace", typeof(string)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Name", typeof(string)),
                new VectorStoreRecordDataProperty("Category", typeof(string)),
                new VectorStoreRecordDataProperty("MemoryText", typeof(string)),
                new VectorStoreRecordVectorProperty("MemoryTextEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = vectorDimensions },
            }
        };

        this._vectorStore = vectorStore;
        this._textEmbeddingGenerationService = textEmbeddingGenerationService;
        this._storageNamespace = storageNamespace;
        this._vectorDimensions = vectorDimensions;
        this._vectorStoreRecordCollection = new Lazy<IVectorStoreRecordCollection<TKey, MemoryDocument<TKey>>>(() =>
            this._vectorStore.GetCollection<TKey, MemoryDocument<TKey>>(collectionName, memoryDocumentDefinition));
    }

    /// <inheritdoc/>
    public override async Task<string?> GetMemoryAsync(string documentName, CancellationToken cancellationToken = default)
    {
        var vectorStoreRecordCollection = await this.EnsureCollectionCreatedAsync(cancellationToken).ConfigureAwait(false);

        // If the database supports string keys, get using the namespace + document name.
        if (typeof(TKey) == typeof(string))
        {
            var namespaceKey = $"{this._storageNamespace}:{documentName}";

            var record = await vectorStoreRecordCollection.GetAsync((TKey)(object)namespaceKey, cancellationToken: cancellationToken).ConfigureAwait(false);
            return record?.MemoryText;
        }

        // Otherwise do a search with a filter on the document name and namespace.
        ReadOnlyMemory<float> vector = new(new float[this._vectorDimensions]);
        var searchResult = await vectorStoreRecordCollection.VectorizedSearchAsync(
            vector,
            options: new()
            {
                Top = 1,
                Filter = x => x.Name == documentName && x.Namespace == this._storageNamespace,
            },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var results = await searchResult.Results.ToListAsync(cancellationToken).ConfigureAwait(false);

        if (results.Count == 0)
        {
            return null;
        }

        return results[0].Record.MemoryText;
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<string> SimilaritySearch(string query, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var vectorStoreRecordCollection = await this.EnsureCollectionCreatedAsync(cancellationToken).ConfigureAwait(false);

        var vector = await this._textEmbeddingGenerationService.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);
        var searchResult = await vectorStoreRecordCollection.VectorizedSearchAsync(
            vector,
            options: new()
            {
                Top = 3,
                Filter = x => x.Namespace == this._storageNamespace,
            },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        await foreach (var result in searchResult.Results.ConfigureAwait(false))
        {
            yield return result.Record.MemoryText;
        }
    }

    /// <inheritdoc/>
    public override async Task SaveMemoryAsync(string documentName, string memoryText, CancellationToken cancellationToken = default)
    {
        var vectorStoreRecordCollection = await this.EnsureCollectionCreatedAsync(cancellationToken).ConfigureAwait(false);

        var vector = await this._textEmbeddingGenerationService.GenerateEmbeddingAsync(
            string.IsNullOrWhiteSpace(memoryText) ? "Empty" : memoryText,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var memoryDocument = new MemoryDocument<TKey>
        {
            Key = GenerateUniqueKey<TKey>(this._storageNamespace, documentName),
            Namespace = this._storageNamespace,
            Name = documentName,
            MemoryText = memoryText,
            MemoryTextEmbedding = vector,
        };

        await vectorStoreRecordCollection.UpsertAsync(memoryDocument, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override Task SaveMemoryAsync(string memoryText, CancellationToken cancellationToken = default)
    {
        return this.SaveMemoryAsync(null!, memoryText, cancellationToken);
    }

    /// <summary>
    /// Thread safe method to get the collection and ensure that it is created at least once.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created collection.</returns>
    private async Task<IVectorStoreRecordCollection<TKey, MemoryDocument<TKey>>> EnsureCollectionCreatedAsync(CancellationToken cancellationToken)
    {
        var vectorStoreRecordCollection = this._vectorStoreRecordCollection.Value;

        // Return immediately if the collection is already created, no need to do any locking in this case.
        if (this._collectionInitialized)
        {
            return vectorStoreRecordCollection;
        }

        // Wait on a lock to ensure that only one thread can create the collection.
        await this._collectionInitializationLock.WaitAsync(cancellationToken).ConfigureAwait(false);

        // If multiple threads waited on the lock, and the first already created the collection,
        // we can return immediately without doing any work in subsequent threads.
        if (this._collectionInitialized)
        {
            this._collectionInitializationLock.Release();
            return vectorStoreRecordCollection;
        }

        // Only the winning thread should reach this point and create the collection.
        try
        {
            await vectorStoreRecordCollection.CreateCollectionIfNotExistsAsync(cancellationToken).ConfigureAwait(false);
            this._collectionInitialized = true;
        }
        finally
        {
            this._collectionInitializationLock.Release();
        }

        return vectorStoreRecordCollection;
    }

    /// <summary>
    /// Generates a unique key for the memory document.
    /// </summary>
    /// <param name="storageNamespace">Storage namespace to use for string keys.</param>
    /// <param name="documentName">An optional document name to use for the key if the database supports string keys.</param>
    /// <typeparam name="TDocumentKey">The type of the key to use, since different databases require/support different keys.</typeparam>
    /// <returns>A new unique key.</returns>
    /// <exception cref="NotSupportedException">Thrown if the requested key type is not supported.</exception>
    private static TDocumentKey GenerateUniqueKey<TDocumentKey>(string storageNamespace, string? documentName)
        => typeof(TDocumentKey) switch
        {
            _ when typeof(TDocumentKey) == typeof(string) && documentName is not null => (TDocumentKey)(object)$"{storageNamespace}:{documentName}",
            _ when typeof(TDocumentKey) == typeof(string) => (TDocumentKey)(object)Guid.NewGuid().ToString(),
            _ when typeof(TDocumentKey) == typeof(Guid) => (TDocumentKey)(object)Guid.NewGuid(),

            _ => throw new NotSupportedException($"Unsupported key of type '{typeof(TDocumentKey).Name}'")
        };

    /// <summary>
    /// The data model to use for storing memory documents in the vector store.
    /// </summary>
    /// <typeparam name="TDocumentKey">The type of the key to use, since different databases require/support different keys.</typeparam>
    private sealed class MemoryDocument<TDocumentKey>
    {
        /// <summary>
        /// Gets or sets a unique identifier for the memory document.
        /// </summary>
        public TDocumentKey Key { get; set; } = default!;

        /// <summary>
        /// Gets or sets the namespace for the memory document.
        /// </summary>
        /// <remarks>
        /// A namespace is a logical grouping of memory documents, e.g. may include a user id to scope the memory to a specific user.
        /// </remarks>
        public string Namespace { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets an optional name for the memory document.
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets an optional category for the memory document.
        /// </summary>
        public string Category { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the actual memory content as text.
        /// </summary>
        public string MemoryText { get; set; } = string.Empty;

        public ReadOnlyMemory<float> MemoryTextEmbedding { get; set; }
    }

    /// <inheritdoc/>
    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._collectionInitializationLock.Dispose();
            }

            this._disposedValue = true;
        }
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
