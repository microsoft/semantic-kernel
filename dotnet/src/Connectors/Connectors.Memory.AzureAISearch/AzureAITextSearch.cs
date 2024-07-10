// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// An Azure Search service that creates and recalls memories associated with text.
/// </summary>
public sealed class AzureAITextSearch : ITextSearch<TextSearchResult>, ITextSearch<SearchDocument>, ITextSearch<string>
{
    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearch"/> connector with API key authentication.
    /// </summary>
    /// <param name="endpoint">Required. The URI endpoint of the Search service. This is likely to be similar to "https://{search_service}.search.windows.net". The URI must use HTTPS.</param>
    /// <param name="adminKey">
    /// Required. The API key credential used to authenticate requests against the Search service.
    /// You need to use an admin key to perform any operations on the SearchIndexClient.
    /// See <see href="https://docs.microsoft.com/azure/search/search-security-api-keys">Create and manage api-keys for an Azure Cognitive Search service</see> for more information about API keys in Azure Cognitive Search.
    /// </param>
    /// <param name="indexName">The name of the search index.</param>
    /// <param name="options">Options used when creating this instance of <see cref="AzureAITextSearch"/>.</param>
    public AzureAITextSearch(string endpoint, string adminKey, string indexName, AzureAITextSearchOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(adminKey);
        Verify.NotNullOrWhiteSpace(indexName);

        this._searchIndexClient = new SearchIndexClient(new Uri(endpoint), new AzureKeyCredential(adminKey));
        this._index = indexName;
        this._mapToString = options?.MapToString ?? DefaultMapToString;
        this._mapToTextSearchResult = options?.MapToTextSearchResult ?? DefaultMapToTextSearchResult;
    }

    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearch"/> connector with provided <see cref="SearchIndexClient"/> instance.
    /// </summary>
    public AzureAITextSearch(SearchIndexClient searchIndexClient, AzureAITextSearchOptions? options = null)
    {
        Verify.NotNull(searchIndexClient);

        this._searchIndexClient = searchIndexClient;
        this._mapToString = options?.MapToString ?? DefaultMapToString;
        this._mapToTextSearchResult = options?.MapToTextSearchResult ?? DefaultMapToTextSearchResult;
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<TextSearchResult>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(true);

        if (response == null)
        {
            return new KernelSearchResults<TextSearchResult>(null, AsyncEnumerable.Empty<TextSearchResult>(), 0, null);
        }

        return new KernelSearchResults<TextSearchResult>(response, this.GetResultsAsTextSearchResultAsync(response, cancellationToken), response.Value.TotalCount, GetResultsMetadata(response));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<SearchDocument>> ITextSearch<SearchDocument>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(true);

        if (response == null)
        {
            return new KernelSearchResults<SearchDocument>(null, AsyncEnumerable.Empty<SearchDocument>(), 0, null);
        }

        return new KernelSearchResults<SearchDocument>(response, this.GetResultsAsSearchDocumentAsync(response, cancellationToken), response.Value.TotalCount, GetResultsMetadata(response));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<string>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(true);

        if (response == null)
        {
            return new KernelSearchResults<string>(null, AsyncEnumerable.Empty<string>(), 0, null);
        }

        return new KernelSearchResults<string>(response, this.GetResultsAsStringAsync(response, cancellationToken), response.Value.TotalCount, GetResultsMetadata(response));
    }

    #region private

    private readonly SearchIndexClient _searchIndexClient;
    private readonly string? _index;
    private readonly MapSearchDocumentToString _mapToString;
    private readonly MapSearchDocumentToTextSearchResult _mapToTextSearchResult;

    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">What to search for</param>
    /// <param name="searchOptions">Option search execution settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<Response<SearchResults<SearchDocument>>?> ExecuteSearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(query);

        var index = searchOptions?.Index ?? this._index;
        Verify.NotNullOrWhiteSpace(index);

        var indexName = this.NormalizeIndexName(index);
        var searchClient = this._searchIndexClient.GetSearchClient(indexName);

        var azureSearchOptions = this.CreateAzureSearchOptions(searchOptions);

        //SearchResults<T>? searchResults = null;
        try
        {
            return await searchClient.SearchAsync<SearchDocument>(query, azureSearchOptions, cancellationToken).ConfigureAwait(true);
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // index not found, no data to return
        }

        return null;
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="searchResults">Response containing the documents matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<SearchDocument> GetResultsAsSearchDocumentAsync(SearchResults<SearchDocument>? searchResults, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResults == null)
        {
            yield break;
        }

        await foreach (SearchResult<SearchDocument> searchResult in searchResults.GetResultsAsync().ConfigureAwait(false))
        {
            yield return searchResult.Document;
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="response">Response containing the documents matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(Response<SearchResults<SearchDocument>> response, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (response == null)
        {
            yield break;
        }

        await foreach (SearchResult<SearchDocument> searchResult in response.Value.GetResultsAsync().ConfigureAwait(false))
        {
            yield return this._mapToString(searchResult.Document);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="response">Response containing the documents matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(Response<SearchResults<SearchDocument>> response, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (response is null)
        {
            yield break;
        }

        await foreach (SearchResult<SearchDocument> searchResult in response.Value.GetResultsAsync().ConfigureAwait(false))
        {
            yield return this._mapToTextSearchResult(searchResult.Document);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="response">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(Response<SearchResults<SearchDocument>> response)
    {
        return new Dictionary<string, object?>()
        {
            { "Coverage", response.Value.Coverage },
        };
    }

    /// <summary>
    /// Index names cannot contain special chars. We use this rule to replace a few common ones
    /// with an underscore and reduce the chance of errors. If other special chars are used, we leave it
    /// to the service to throw an error.
    /// Note:
    /// - replacing chars introduces a small chance of conflicts, e.g. "the-user" and "the_user".
    /// - we should consider whether making this optional and leave it to the developer to handle.
    /// </summary>
    private static readonly Regex s_replaceIndexNameSymbolsRegex = new(@"[\s|\\|/|.|_|:]");

    /// <summary>
    /// Normalize index name to match Azure AI Search rules.
    /// The method doesn't handle all the error scenarios, leaving it to the service
    /// to throw an error for edge cases not handled locally.
    /// </summary>
    /// <param name="indexName">Value to normalize</param>
    /// <param name="parameterName">The name of the argument used with <paramref name="indexName"/>.</param>
    /// <returns>Normalized name</returns>
    private string NormalizeIndexName(string indexName, [CallerArgumentExpression(nameof(indexName))] string? parameterName = null)
    {
        if (indexName.Length > 128)
        {
            throw new ArgumentOutOfRangeException(parameterName, "The collection name is too long, it cannot exceed 128 chars.");
        }

#pragma warning disable CA1308 // The service expects a lowercase string
        indexName = indexName.ToLowerInvariant();
#pragma warning restore CA1308

        return s_replaceIndexNameSymbolsRegex.Replace(indexName.Trim(), "-");
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="SearchDocument"/> to a <see cref="string"/>
    /// </summary>
    private static string DefaultMapToString(SearchDocument document)
    {
        return JsonSerializer.Serialize(document);
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="SearchDocument"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private static TextSearchResult DefaultMapToTextSearchResult(SearchDocument document)
    {
        document.TryGetValue("title", out var name);
        document.TryGetValue("chunk", out var value);
        return new TextSearchResult(name: name?.ToString() ?? string.Empty, value: value?.ToString() ?? string.Empty, innerResult: document);
    }

    /// <summary>
    /// Create instance of <see cref="Azure.Search.Documents.SearchOptions"/> from <see cref="SearchOptions"/>
    /// </summary>
    private Azure.Search.Documents.SearchOptions CreateAzureSearchOptions(SearchOptions? searchOptions)
    {
        return new Azure.Search.Documents.SearchOptions()
        {
            QueryType = SearchQueryType.Simple,
            IncludeTotalCount = true,
            Size = searchOptions?.Count ?? 1,
            Skip = searchOptions?.Offset ?? 0,
        };
    }

    #endregion
}
