// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
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
public class AzureAITextSearchService : ITextSearchService
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearchService"/> connector with API key authentication.
    /// </summary>
    /// <param name="endpoint">Required. The URI endpoint of the Search service. This is likely to be similar to "https://{search_service}.search.windows.net". The URI must use HTTPS.</param>
    /// <param name="adminKey">
    /// Required. The API key credential used to authenticate requests against the Search service.
    /// You need to use an admin key to perform any operations on the SearchIndexClient.
    /// See <see href="https://docs.microsoft.com/azure/search/search-security-api-keys">Create and manage api-keys for an Azure Cognitive Search service</see> for more information about API keys in Azure Cognitive Search.
    /// </param>
    public AzureAITextSearchService(string endpoint, string adminKey)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(adminKey);

        this._searchIndexClient = new SearchIndexClient(new Uri(endpoint), new AzureKeyCredential(adminKey));

        this._attributes = new Dictionary<string, object?>
        {
            { "ServiceName", this._searchIndexClient.ServiceName },
        };
    }

    /// <summary>
    /// Create an instance of the <see cref="AzureAITextSearchService"/> connector with provided <see cref="SearchIndexClient"/> instance.
    /// </summary>
    public AzureAITextSearchService(SearchIndexClient searchIndexClient)
    {
        Verify.NotNull(searchIndexClient);

        this._searchIndexClient = searchIndexClient;

        this._attributes = new Dictionary<string, object?>
        {
            { "ServiceName", this._searchIndexClient.ServiceName },
        };
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<T>> SearchAsync<T>(string query, SearchExecutionSettings searchSettings, CancellationToken cancellationToken = default) where T : class
    {
        Verify.NotNullOrWhiteSpace(query);
        Verify.NotNull(searchSettings);

        var indexName = this.NormalizeIndexName(searchSettings.Index);
        var searchClient = this._searchIndexClient.GetSearchClient(indexName);

        var azureSearchSettings = AzureAISearchExecutionSettings.FromExecutionSettings(searchSettings);

        SearchResults<T>? searchResults = null;
        try
        {
            searchResults = await searchClient.SearchAsync<T>(query, azureSearchSettings.SearchOptions, cancellationToken).ConfigureAwait(true);
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // index not found, no data to return
        }

        return new KernelSearchResults<T>(searchResults, this.GetResultsAsync(searchResults, cancellationToken), searchResults?.TotalCount, GetResultsMetadata(searchResults));
    }

    #region private

    private readonly SearchIndexClient _searchIndexClient;
    private readonly IReadOnlyDictionary<string, object?> _attributes;

    /// <summary>
    /// Return the search results and associated metadata.
    /// </summary>
    /// <typeparam name="T">The .NET type that maps to the index schema. Instances of this type
    /// can be retrieved as documents from the index.</typeparam>
    /// <param name="searchResults">Response containing the documents matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<KernelSearchResult<T>> GetResultsAsync<T>(SearchResults<T>? searchResults, [EnumeratorCancellation] CancellationToken cancellationToken) where T : class
    {
        if (searchResults == null)
        {
            yield break;
        }

        await foreach (SearchResult<T> searchResult in searchResults.GetResultsAsync())
        {
            yield return new AzureAIKernelSearchResult<T>(searchResult);
        }
    }

    static private Dictionary<string, object?>? GetResultsMetadata<T>(SearchResults<T>? searchResults) where T : class
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
