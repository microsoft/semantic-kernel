// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A Vector Store Text Search implementation that can be used to perform searches using a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreTextSearch<TRecord> : ITextSearch
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : class
{
    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorizedSearch{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorizedSearch"><see cref="IVectorizedSearch{TRecord}"/> instance used to perform the search.</param>
    /// <param name="textEmbeddingGeneration"><see cref="ITextEmbeddingGenerationService"/> instance used to create a vector from the text query.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorizedSearch<TRecord> vectorizedSearch,
        ITextEmbeddingGenerationService textEmbeddingGeneration,
        ITextSearchStringMapper stringMapper,
        ITextSearchResultMapper resultMapper,
        VectorStoreTextSearchOptions? options = null)
    {
        Verify.NotNull(vectorizedSearch);
        Verify.NotNull(textEmbeddingGeneration);
        Verify.NotNull(stringMapper);
        Verify.NotNull(resultMapper);

        this._vectorizedSearch = vectorizedSearch;
        this._textEmbeddingGeneration = textEmbeddingGeneration;
        this._stringMapper = stringMapper;
        this._resultMapper = resultMapper;
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorizableTextSearch{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorizableTextSearch"><see cref="IVectorizableTextSearch{TRecord}"/> instance used to perform the text search.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorizableTextSearch<TRecord> vectorizableTextSearch,
        ITextSearchStringMapper stringMapper,
        ITextSearchResultMapper resultMapper,
        VectorStoreTextSearchOptions? options = null)
    {
        Verify.NotNull(vectorizableTextSearch);
        Verify.NotNull(stringMapper);
        Verify.NotNull(resultMapper);

        this._vectorizableTextSearch = vectorizableTextSearch;
        this._stringMapper = stringMapper;
        this._resultMapper = resultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        IAsyncEnumerable<VectorSearchResult<TRecord>> searchResponse = await this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        IAsyncEnumerable<VectorSearchResult<TRecord>> searchResponse = await this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        IAsyncEnumerable<VectorSearchResult<TRecord>> searchResponse = await this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetResultsAsRecordAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region private
    private readonly IVectorizedSearch<TRecord>? _vectorizedSearch;
    private readonly ITextEmbeddingGenerationService? _textEmbeddingGeneration;
    private readonly IVectorizableTextSearch<TRecord>? _vectorizableTextSearch;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    /// <summary>
    /// Execute a vector search and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<IAsyncEnumerable<VectorSearchResult<TRecord>>> ExecuteVectorSearchAsync(string query, TextSearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        searchOptions ??= new TextSearchOptions();
        var vectorSearchOptions = new VectorSearchOptions
        {
            Filter = null,
            Offset = searchOptions.Offset,
            Limit = searchOptions.Count,
        };

        if (this._vectorizedSearch is not null)
        {
            var vectorizedQuery = await this._textEmbeddingGeneration!.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);

            return this._vectorizedSearch.VectorizedSearchAsync(vectorizedQuery, vectorSearchOptions, cancellationToken);
        }

        return this._vectorizableTextSearch!.VectorizableTextSearchAsync(query, vectorSearchOptions, cancellationToken);
    }

    /// <summary>
    /// Return the search results as instances of TRecord.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsRecordAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return result.Record;
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(result.Record);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return this._stringMapper.MapFromResultToString(result.Record);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse)
    {
        return [];
    }

    #endregion
}
