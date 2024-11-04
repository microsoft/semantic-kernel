// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory.VectorStoreEmbeddingGeneration;

/// <summary>
/// Decorator for a <see cref="IVectorStore"/> that generates embeddings for records on upsert.
/// </summary>
/// <remarks>
/// This class is part of the <see cref="VectorStore_EmbeddingGeneration"/> sample.
/// </remarks>
public class TextEmbeddingVectorStore : IVectorStore
{
    /// <summary>The decorated <see cref="IVectorStore"/>.</summary>
    private readonly IVectorStore _decoratedVectorStore;

    /// <summary>The service to use for generating the embeddings.</summary>
    private readonly ITextEmbeddingGenerationService _textEmbeddingGenerationService;

    /// <summary>
    /// Initializes a new instance of the <see cref="TextEmbeddingVectorStore"/> class.
    /// </summary>
    /// <param name="decoratedVectorStore">The decorated <see cref="IVectorStore"/>.</param>
    /// <param name="textEmbeddingGenerationService">The service to use for generating the embeddings.</param>
    public TextEmbeddingVectorStore(IVectorStore decoratedVectorStore, ITextEmbeddingGenerationService textEmbeddingGenerationService)
    {
        // Verify & Assign.
        this._decoratedVectorStore = decoratedVectorStore ?? throw new ArgumentNullException(nameof(decoratedVectorStore));
        this._textEmbeddingGenerationService = textEmbeddingGenerationService ?? throw new ArgumentNullException(nameof(textEmbeddingGenerationService));
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
        var collection = this._decoratedVectorStore.GetCollection<TKey, TRecord>(name, vectorStoreRecordDefinition);
        var embeddingStore = new TextEmbeddingVectorStoreRecordCollection<TKey, TRecord>(collection, this._textEmbeddingGenerationService);
        return embeddingStore;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this._decoratedVectorStore.ListCollectionNamesAsync(cancellationToken);
    }
}
