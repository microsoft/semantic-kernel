// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// A Tavily Text Search implementation that can be used to perform searches using the Tavily Web Search API.
/// </summary>
public sealed class TavilyTextSearch : ITextSearch
{
    /// <summary>
    /// Create an instance of the <see cref="TavilyTextSearch"/> with API key authentication.
    /// </summary>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Options used when creating this instance of <see cref="TavilyTextSearch"/>.</param>
    public TavilyTextSearch(string apiKey, TavilyTextSearchOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
        this._uri = options?.Endpoint ?? new Uri(DefaultUri);
        this._searchOptions = options;
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(TavilyTextSearch)) ?? NullLogger.Instance;
        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(TavilyTextSearch)));
        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetSearchResultsAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private readonly TavilyTextSearchOptions? _searchOptions;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    private const string DefaultUri = "https://api.tavily.com/search";

    private const string Topic = "topic";
    private const string TimeRange = "time_range";
    private const string Days = "days";
    private const string IncludeDomain = "include_domain";
    private const string ExcludeDomain = "exclude_domain";

    private static readonly string[] s_validFieldNames = [Topic, TimeRange, Days, IncludeDomain, ExcludeDomain];

    /// <summary>
    /// Execute a Tavily search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<TavilySearchResponse?> ExecuteSearchAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        return JsonSerializer.Deserialize<TavilySearchResponse>(json);
    }

    /// <summary>
    /// Sends a POST request to the specified URI.
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="searchOptions">The search options.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken)
    {
        if (searchOptions.Top is <= 0 or > 50)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions, $"{nameof(searchOptions)} count value must be greater than 0 and have a maximum value of 50.");
        }

        var requestContent = this.BuildRequestContent(query, searchOptions);

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Post, this._uri)
        {
            Content = GetJsonContent(requestContent)
        };

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TavilySearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetSearchResultsAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return result;
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return image;
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(result);
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return this._resultMapper.MapFromResultToTextSearchResult(image);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        if (this._searchOptions?.IncludeAnswer ?? false)
        {
            yield return searchResponse.Answer ?? string.Empty;
            await Task.Yield();
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._stringMapper.MapFromResultToString(result);
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return this._stringMapper.MapFromResultToString(image);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(TavilySearchResponse? searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "ResponseTime", searchResponse?.ResponseTime },
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="TavilySearchResult"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is TavilySearchResult searchResult)
            {
                return searchResult.RawContent ?? searchResult.Content ?? string.Empty;
            }
            else if (result is TavilyImageResult imageResult)
            {
                return imageResult.Description ?? string.Empty;
            }
            throw new ArgumentException("Result must be a TavilySearchResult", nameof(result));
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="TavilySearchResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is TavilySearchResult searchResult)
            {
                return new TextSearchResult(searchResult.RawContent ?? searchResult.Content ?? string.Empty) { Name = searchResult.Title, Link = searchResult.Url };
            }
            else if (result is TavilyImageResult imageResult)
            {
                var uri = new Uri(imageResult.Url);
                var name = uri.Segments[^1];
                return new TextSearchResult(imageResult.Description ?? string.Empty) { Name = name, Link = imageResult.Url };
            }
            throw new ArgumentException("Result must be a TavilySearchResult", nameof(result));
        }
    }

#pragma warning disable CS0618 // FilterClause is obsolete
    /// <summary>
    /// Build a query string from the <see cref="TextSearchOptions"/>
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="searchOptions">The search options.</param>
    private TavilySearchRequest BuildRequestContent(string query, TextSearchOptions searchOptions)
    {
        string? topic = null;
        string? timeRange = null;
        int? days = null;
        int? maxResults = searchOptions.Top - searchOptions.Skip;
        IList<string>? includeDomains = null;
        IList<string>? excludeDomains = null;

        if (searchOptions.Filter is not null)
        {
            var filterClauses = searchOptions.Filter.FilterClauses;

            foreach (var filterClause in filterClauses)
            {
                if (filterClause is EqualToFilterClause equalityFilterClause)
                {
                    if (equalityFilterClause.FieldName.Equals(Topic, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        topic = equalityFilterClause.Value.ToString()!;
                    }
                    else if (equalityFilterClause.FieldName.Equals(TimeRange, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        timeRange = equalityFilterClause.Value.ToString()!;
                    }
                    else if (equalityFilterClause.FieldName.Equals(Days, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        days = Convert.ToInt32(equalityFilterClause.Value);
                    }
                    else if (equalityFilterClause.FieldName.Equals(IncludeDomain, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        var includeDomain = equalityFilterClause.Value.ToString()!;
                        includeDomains ??= [];
                        includeDomains.Add(includeDomain);
                    }
                    else if (equalityFilterClause.FieldName.Equals(ExcludeDomain, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        var excludeDomain = equalityFilterClause.Value.ToString()!;
                        excludeDomains ??= [];
                        excludeDomains.Add(excludeDomain);
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name '{equalityFilterClause.FieldName}', must be one of {string.Join(",", s_validFieldNames)}", nameof(searchOptions));
                    }
                }
            }
        }

        return new TavilySearchRequest(
            query,
            topic,
            timeRange,
            days,
#pragma warning disable CA1308 // Lower is preferred over uppercase
            this._searchOptions?.SearchDepth?.ToString()?.ToLowerInvariant(),
#pragma warning restore CA1308
            this._searchOptions?.ChunksPerSource,
            this._searchOptions?.IncludeImages,
            this._searchOptions?.IncludeImageDescriptions,
            this._searchOptions?.IncludeAnswer,
            this._searchOptions?.IncludeRawContent,
            maxResults,
            includeDomains,
            excludeDomains);
    }
#pragma warning restore CS0618 // FilterClause is obsolete

    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private static StringContent? GetJsonContent(object? payload)
    {
        if (payload is null)
        {
            return null;
        }

        string strPayload = payload as string ?? JsonSerializer.Serialize(payload, s_jsonOptionsCache);
        return new(strPayload, Encoding.UTF8, "application/json");
    }
    #endregion
}
