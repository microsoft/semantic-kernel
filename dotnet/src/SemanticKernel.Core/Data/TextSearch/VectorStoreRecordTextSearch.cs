// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A Vector Store Text Search implementation that can be used to perform searches using a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreRecordTextSearch<TRecord> : ITextSearch
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : class
{
    /// <summary>
    /// Create an instance of the <see cref="VectorStoreRecordTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearch{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearch"></param>
    /// <param name="textEmbeddingGeneration"></param>
    /// <param name="options"></param>
    public VectorStoreRecordTextSearch(
        IVectorSearch<TRecord> vectorSearch,
        ITextEmbeddingGenerationService textEmbeddingGeneration,
        VectorStoreRecordTextSearchOptions? options = null)
    {
        Verify.NotNull(vectorSearch);
        Verify.NotNull(textEmbeddingGeneration);

        this._vectorSearch = vectorSearch;
        this._textEmbeddingGeneration = textEmbeddingGeneration;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var vectorSearchOptions = new VectorSearchOptions
        {
            Filter = null,
            Offset = searchOptions.Offset,
            Limit = searchOptions.Count,
        };

        var vector = await this._textEmbeddingGeneration.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);
        var vectorQuery = VectorSearchQuery.CreateQuery(vector);

        var searchResponse = this._vectorSearch.SearchAsync(vectorQuery, vectorSearchOptions, cancellationToken);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    #region private
    private readonly IVectorSearch<TRecord> _vectorSearch;
    private readonly ITextEmbeddingGenerationService _textEmbeddingGeneration;

    /// <summary>
    /// Return the search results as instances of <see cref="BingWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsWebPageAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return webPage;
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
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(webPage);
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
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return this._stringMapper.MapFromResultToString(webPage);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <typeparam name="T">The .NET type that maps to the index schema. Instances of this type
    /// can be retrieved as documents from the index.</typeparam>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata<T>(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse) where T : class
    {
        return new Dictionary<string, object?>()
        {
            { "AlteredQuery", searchResponse?.QueryContext?.AlteredQuery },
        };
    }

    #endregion
}
