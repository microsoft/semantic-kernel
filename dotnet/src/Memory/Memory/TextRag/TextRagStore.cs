// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory.TextRag;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A class that allows for easy storage and retrieval of documents in a Vector Store for Retrieval Augmented Generation (RAG).
/// </summary>
/// <typeparam name="TKey">The key type to use with the vector store.</typeparam>
public class TextRagStore<TKey> : ITextSearch, IDisposable
    where TKey : notnull
{
    private readonly IVectorStore _vectorStore;
    private readonly ITextEmbeddingGenerationService _textEmbeddingGenerationService;
    private readonly int _vectorDimensions;
    private readonly string? _searchNamespace;

    private readonly Lazy<IVectorStoreRecordCollection<TKey, TextRagStorageDocument<TKey>>> _vectorStoreRecordCollection;
    private readonly SemaphoreSlim _collectionInitializationLock = new(1, 1);
    private bool _collectionInitialized = false;
    private bool _disposedValue;

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorDataTextMemoryStore{TKey}"/> class.
    /// </summary>
    /// <param name="vectorStore">The vector store to store and read the memories from.</param>
    /// <param name="textEmbeddingGenerationService">The service to use for generating embeddings for the memories.</param>
    /// <param name="collectionName">The name of the collection in the vector store to store and read the memories from.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="searchNamespace">An optional namespace to filter search results to.</param>
    /// <exception cref="NotSupportedException">Thrown if the key type provided is not supported.</exception>
    public TextRagStore(IVectorStore vectorStore, ITextEmbeddingGenerationService textEmbeddingGenerationService, string collectionName, int vectorDimensions, string? searchNamespace)
    {
        Verify.NotNull(vectorStore);
        Verify.NotNull(textEmbeddingGenerationService);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");

        this._vectorStore = vectorStore;
        this._textEmbeddingGenerationService = textEmbeddingGenerationService;
        this._vectorDimensions = vectorDimensions;
        this._searchNamespace = searchNamespace;

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(Guid))
        {
            throw new NotSupportedException($"Unsupported key of type '{typeof(TKey).Name}'");
        }

        VectorStoreRecordDefinition ragDocumentDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>()
            {
                new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                new VectorStoreRecordDataProperty("Namespaces", typeof(List<string>)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("SourceId", typeof(string)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Text", typeof(string)),
                new VectorStoreRecordDataProperty("SourceName", typeof(string)),
                new VectorStoreRecordDataProperty("SourceReference", typeof(string)),
                new VectorStoreRecordVectorProperty("TextEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = vectorDimensions },
            }
        };

        this._vectorStoreRecordCollection = new Lazy<IVectorStoreRecordCollection<TKey, TextRagStorageDocument<TKey>>>(() =>
            this._vectorStore.GetCollection<TKey, TextRagStorageDocument<TKey>>(collectionName, ragDocumentDefinition));
    }

    /// <summary>
    /// Upserts a batch of documents into the vector store.
    /// </summary>
    /// <param name="documents">The documents to upload.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the documents have been upserted.</returns>
    public async Task UpsertDocumentsAsync(IEnumerable<TextRagDocument> documents, CancellationToken cancellationToken = default)
    {
        var vectorStoreRecordCollection = await this.EnsureCollectionCreatedAsync(cancellationToken).ConfigureAwait(false);

        var storageDocumentsTasks = documents.Select(async document =>
        {
            var key = GenerateUniqueKey<TKey>(document.SourceId);
            var textEmbedding = await this._textEmbeddingGenerationService.GenerateEmbeddingAsync(document.Text).ConfigureAwait(false);

            return new TextRagStorageDocument<TKey>
            {
                Key = key,
                Namespaces = document.Namespaces,
                SourceId = document.SourceId,
                Text = document.Text,
                SourceName = document.SourceName,
                SourceReference = document.SourceReference,
                TextEmbedding = textEmbedding
            };
        });

        var storageDocuments = await Task.WhenAll(storageDocumentsTasks).ConfigureAwait(false);
        await vectorStoreRecordCollection.UpsertBatchAsync(storageDocuments, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResult = await this.SearchInternalAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        return new(searchResult.Results.Select(x => x.Record.Text ?? string.Empty));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResult = await this.SearchInternalAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        var results = searchResult.Results.Select(x => new TextSearchResult(x.Record.Text ?? string.Empty) { Name = x.Record.SourceName, Link = x.Record.SourceReference });
        return new(searchResult.Results.Select(x =>
            new TextSearchResult(x.Record.Text ?? string.Empty)
            {
                Name = x.Record.SourceName,
                Link = x.Record.SourceReference
            }));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResult = await this.SearchInternalAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);
        return new(searchResult.Results.Cast<object>());
    }

    /// <summary>
    /// Internal search implementation.
    /// </summary>
    /// <param name="query">The text query to find similar documents to.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The search results.</returns>
    private async Task<VectorSearchResults<TextRagStorageDocument<TKey>>> SearchInternalAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var vectorStoreRecordCollection = await this.EnsureCollectionCreatedAsync(cancellationToken).ConfigureAwait(false);

        // Optional filter to limit the search to a specific namespace.
        Expression<Func<TextRagStorageDocument<TKey>, bool>>? filter = string.IsNullOrWhiteSpace(this._searchNamespace) ? null : x => x.Namespaces.Contains(this._searchNamespace);

        var vector = await this._textEmbeddingGenerationService.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);
        var searchResult = await vectorStoreRecordCollection.VectorizedSearchAsync(
            vector,
            options: new()
            {
                Top = searchOptions?.Top ?? 3,
                Filter = filter,
            },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return searchResult;
    }

    /// <summary>
    /// Thread safe method to get the collection and ensure that it is created at least once.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created collection.</returns>
    private async Task<IVectorStoreRecordCollection<TKey, TextRagStorageDocument<TKey>>> EnsureCollectionCreatedAsync(CancellationToken cancellationToken)
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
    /// Generates a unique key for the RAG document.
    /// </summary>
    /// <param name="sourceId">Source id of the source document for this RAG document.</param>
    /// <typeparam name="TDocumentKey">The type of the key to use, since different databases require/support different keys.</typeparam>
    /// <returns>A new unique key.</returns>
    /// <exception cref="NotSupportedException">Thrown if the requested key type is not supported.</exception>
    private static TDocumentKey GenerateUniqueKey<TDocumentKey>(string? sourceId)
        => typeof(TDocumentKey) switch
        {
            _ when typeof(TDocumentKey) == typeof(string) && !string.IsNullOrWhiteSpace(sourceId) => (TDocumentKey)(object)sourceId!,
            _ when typeof(TDocumentKey) == typeof(string) => (TDocumentKey)(object)Guid.NewGuid().ToString(),
            _ when typeof(TDocumentKey) == typeof(Guid) => (TDocumentKey)(object)Guid.NewGuid(),

            _ => throw new NotSupportedException($"Unsupported key of type '{typeof(TDocumentKey).Name}'")
        };

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

    /// <summary>
    /// The data model to use for storing RAG documents in the vector store.
    /// </summary>
    /// <typeparam name="TDocumentKey">The type of the key to use, since different databases require/support different keys.</typeparam>
    private sealed class TextRagStorageDocument<TDocumentKey>
    {
        /// <summary>
        /// Gets or sets a unique identifier for the memory document.
        /// </summary>
        public TDocumentKey Key { get; set; } = default!;

        /// <summary>
        /// Gets or sets an optional list of namespaces that the document should belong to.
        /// </summary>
        /// <remarks>
        /// A namespace is a logical grouping of documents, e.g. may include a group id to scope the document to a specific group of users.
        /// </remarks>
        public List<string> Namespaces { get; set; } = [];

        /// <summary>
        /// Gets or sets an optional source ID for the document.
        /// </summary>
        /// <remarks>
        /// This ID should be unique within the collection that the document is stored in, and can
        /// be used to map back to the source artifact for this document.
        /// If updates need to be made later or the source document was deleted and this document
        /// also needs to be deleted, this id can be used to find the document again.
        /// </remarks>
        public string? SourceId { get; set; }

        /// <summary>
        /// Gets or sets the content as text.
        /// </summary>
        public string? Text { get; set; }

        /// <summary>
        /// Gets or sets an optional name for the source document.
        /// </summary>
        /// <remarks>
        /// This can be used to provide display names for citation links when the document is referenced as
        /// part of a response to a query.
        /// </remarks>
        public string? SourceName { get; set; }

        /// <summary>
        /// Gets or sets an optional reference back to the source of the document.
        /// </summary>
        /// <remarks>
        /// This can be used to provide citation links when the document is referenced as
        /// part of a response to a query.
        /// </remarks>
        public string? SourceReference { get; set; }

        /// <summary>
        /// Gets or sets the embedding for the text content.
        /// </summary>
        public ReadOnlyMemory<float> TextEmbedding { get; set; }
    }
}
