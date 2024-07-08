// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
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
public sealed class AzureAITextSearchService : ITextSearchService<TextSearchResult>, ITextSearchService<SearchDocument>
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; }

    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearchService"/> connector with API key authentication.
    /// </summary>
    /// <param name="endpoint">Required. The URI endpoint of the Search service. This is likely to be similar to "https://{search_service}.search.windows.net". The URI must use HTTPS.</param>
    /// <param name="adminKey">
    /// Required. The API key credential used to authenticate requests against the Search service.
    /// You need to use an admin key to perform any operations on the SearchIndexClient.
    /// See <see href="https://docs.microsoft.com/azure/search/search-security-api-keys">Create and manage api-keys for an Azure Cognitive Search service</see> for more information about API keys in Azure Cognitive Search.
    /// </param>
    /// <param name="index">The name of the search index.</param>
    public AzureAITextSearchService(string endpoint, string adminKey, string? index = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(adminKey);

        this._searchIndexClient = new SearchIndexClient(new Uri(endpoint), new AzureKeyCredential(adminKey));

        this.Attributes = new Dictionary<string, object?>
        {
            { "ServiceName", this._searchIndexClient.ServiceName },
        };

        this._index = index;
    }

    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearchService"/> connector with provided <see cref="SearchIndexClient"/> instance.
    /// </summary>
    public AzureAITextSearchService(SearchIndexClient searchIndexClient)
    {
        Verify.NotNull(searchIndexClient);

        this._searchIndexClient = searchIndexClient;

        this.Attributes = new Dictionary<string, object?>
        {
            { "ServiceName", this._searchIndexClient.ServiceName },
        };
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearchService<TextSearchResult>.SearchAsync(string query, SearchExecutionSettings? searchSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        return await this.ExecuteSearchAsync<TextSearchResult>(query, searchSettings, kernel, cancellationToken).ConfigureAwait(true);
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<SearchDocument>> ITextSearchService<SearchDocument>.SearchAsync(string query, SearchExecutionSettings? searchSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        return await this.ExecuteSearchAsync<SearchDocument>(query, searchSettings, kernel, cancellationToken).ConfigureAwait(true);
    }

    #region private

    private readonly SearchIndexClient _searchIndexClient;
    private readonly string? _index;

    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">What to search for</param>
    /// <param name="searchSettings">Option search execution settings</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<KernelSearchResults<T>> ExecuteSearchAsync<T>(string query, SearchExecutionSettings? searchSettings, Kernel? kernel, CancellationToken cancellationToken) where T : class
    {
        Verify.NotNullOrWhiteSpace(query);
        Verify.NotNull(searchSettings);

        var index = searchSettings.Index ?? this._index;
        Verify.NotNullOrWhiteSpace(index);

        var indexName = this.NormalizeIndexName(index);
        var searchClient = this._searchIndexClient.GetSearchClient(indexName);

        var azureSearchSettings = AzureAISearchExecutionSettings.FromExecutionSettings(searchSettings);

        //SearchResults<T>? searchResults = null;
        try
        {
            var response = await searchClient.SearchAsync<SearchDocument>(query, azureSearchSettings.SearchOptions, cancellationToken).ConfigureAwait(true);
            SearchResults<SearchDocument>? searchResults = response.Value;
            if (typeof(T) == typeof(TextSearchResult))
            {
                return new KernelSearchResults<T>(searchResults, (IAsyncEnumerable<T>)this.GetResultsAsync(searchResults, azureSearchSettings.NameField, azureSearchSettings.ValueField, azureSearchSettings.LinkField, cancellationToken), searchResults?.TotalCount, GetResultsMetadata(searchResults));
            }
            if (typeof(T) == typeof(SearchDocument))
            {
                return new KernelSearchResults<T>(searchResults, (IAsyncEnumerable<T>)this.GetResultsAsync(searchResults, cancellationToken), searchResults?.TotalCount, GetResultsMetadata(searchResults));
            }
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // index not found, no data to return
        }

        return new KernelSearchResults<T>(null, AsyncEnumerable.Empty<T>(), 0, null);
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="searchResults">Response containing the documents matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<SearchDocument> GetResultsAsync(SearchResults<SearchDocument>? searchResults, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResults == null)
        {
            yield break;
        }

        await foreach (SearchResult<SearchDocument> searchResult in searchResults.GetResultsAsync().ConfigureAwait(false))
        {
            yield return searchResult.Document;
        }
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="searchResults">Response containing the documents matching the query.</param>
    /// <param name="nameField">Name of the field that contains the name to return.</param>
    /// <param name="valueField">Name of the field that contains the snippet of text to return.</param>
    /// <param name="linkField">Name of the field that contains the link to return.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsync(SearchResults<SearchDocument>? searchResults, string? nameField, string? valueField, string? linkField, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResults is null)
        {
            yield break;
        }

        Verify.NotNullOrWhiteSpace(nameField, nameof(nameField));
        Verify.NotNullOrWhiteSpace(valueField, nameof(valueField));
        Verify.NotNullOrWhiteSpace(linkField, nameof(nameField));

        await foreach (SearchResult<SearchDocument> searchResult in searchResults.GetResultsAsync().ConfigureAwait(false))
        {
            var name = searchResult.Document.GetString(nameField!);
            var snippet = searchResult.Document.GetString(valueField!);
            var link = searchResult.Document.GetString(linkField!);

            yield return new TextSearchResult(name, snippet, link, searchResult.Document);
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <typeparam name="T">The .NET type that maps to the index schema. Instances of this type
    /// can be retrieved as documents from the index.</typeparam>
    /// <param name="searchResults">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata<T>(SearchResults<T>? searchResults) where T : class
    {
        return new Dictionary<string, object?>()
        {
            { "Coverage", searchResults?.Coverage },
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
    private string NormalizeIndexName(string indexName, [CallerArgumentExpression("indexName")] string? parameterName = null)
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

    #endregion
}
