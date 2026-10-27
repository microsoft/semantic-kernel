// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

internal sealed class TavilySearchRequest
{
    /// <summary>
    /// The search query to execute with Tavily.
    /// </summary>
    [JsonPropertyName("query")]
    [JsonRequired]
    public string Query { get; set; }

    /// <summary>
    /// The category of the search.
    /// Available options: general, news
    /// </summary>
    [JsonPropertyName("topic")]
    public string? Topic { get; set; }

    /// <summary>
    /// The depth of the search. advanced search is tailored to retrieve the
    /// most relevant sources and content snippets for your query,
    /// while basic search provides generic content snippets from each source.
    /// A basic search costs 1 API Credit, while an advanced search costs 2 API Credits.
    /// Available options: basic, advanced
    /// </summary>
    [JsonPropertyName("search_depth")]
    public string? SearchDepth { get; set; }

    /// <summary>
    /// The number of content chunks to retrieve from each source.
    /// Each chunk's length is maximum 500 characters.
    /// Available only when search_depth is advanced.
    /// Required range: 0 - 3
    /// </summary>
    [JsonPropertyName("chunks_per_source")]
    public int? ChunksPerSource { get; set; }

    /// <summary>
    /// The maximum number of search results to return.
    /// Required range: 0 - 20
    /// </summary>
    [JsonPropertyName("max_results")]
    public int? MaxResults { get; set; }

    /// <summary>
    /// The time range back from the current date to filter results.
    /// Available options: day, week, month, year, d, w, m, y
    /// </summary>
    [JsonPropertyName("time_range")]
    public string? TimeRange { get; set; }

    /// <summary>
    /// Number of days back from the current date to include.
    /// Available only if topic is news.
    /// Required range: x >= 0
    /// </summary>
    [JsonPropertyName("days")]
    public int? Days { get; set; }

    /// <summary>
    /// Include an LLM-generated answer to the provided query.
    /// basic or true returns a quick answer. advanced returns a more detailed answer.
    /// </summary>
    [JsonPropertyName("include_answer")]
    public bool? IncludeAnswer { get; set; }

    /// <summary>
    /// Include the cleaned and parsed HTML content of each search result.
    /// </summary>
    [JsonPropertyName("include_raw_content")]
    public bool? IncludeRawContent { get; set; }

    /// <summary>
    /// Also perform an image search and include the results in the response.
    /// </summary>
    [JsonPropertyName("include_images")]
    public bool? IncludeImages { get; set; }

    /// <summary>
    /// When include_images is true, also add a descriptive text for each image.
    /// </summary>
    [JsonPropertyName("include_image_descriptions")]
    public bool? IncludeImageDescriptions { get; set; }

    /// <summary>
    /// Boost search results from a specific country. Available only when topic is general.
    /// </summary>
    [JsonPropertyName("country")]
    public string? Country { get; set; }

    /// <summary>
    /// Return only results after this date. Format: YYYY-MM-DD.
    /// </summary>
    [JsonPropertyName("start_date")]
    public string? StartDate { get; set; }

    /// <summary>
    /// Return only results before this date. Format: YYYY-MM-DD.
    /// </summary>
    [JsonPropertyName("end_date")]
    public string? EndDate { get; set; }

    /// <summary>
    /// Whether to filter out adult or unsafe content from results.
    /// </summary>
    [JsonPropertyName("safe_search")]
    public bool? SafeSearch { get; set; }

    /// <summary>
    /// How include_domains is applied. Available options: restrict, prefer.
    /// </summary>
    [JsonPropertyName("include_domains_mode")]
    public string? IncludeDomainsMode { get; set; }

    /// <summary>
    /// Boost search results in a specific language (ISO 639-1 code or English language name).
    /// </summary>
    [JsonPropertyName("language")]
    public string? Language { get; set; }

    /// <summary>
    /// Strictly filter out results that do not match the language instead of only boosting them.
    /// </summary>
    [JsonPropertyName("filter_by_language")]
    public bool? FilterByLanguage { get; set; }

    /// <summary>
    /// Only return results containing the exact quoted phrase(s) in the query.
    /// </summary>
    [JsonPropertyName("exact_match")]
    public bool? ExactMatch { get; set; }

    /// <summary>
    /// Let Tavily configure search parameters automatically from the query.
    /// </summary>
    [JsonPropertyName("auto_parameters")]
    public bool? AutoParameters { get; set; }

    /// <summary>
    /// A list of domains to specifically include in the search results.
    /// </summary>
    [JsonPropertyName("include_domains")]
    public IList<string>? IncludeDomains { get; set; }

    /// <summary>
    /// A list of domains to specifically exclude from the search results.
    /// </summary>
    [JsonPropertyName("exclude_domains")]
    public IList<string>? ExcludeDomains { get; set; }

    /// <summary>
    /// Additional properties that are not explicitly defined in the schema.
    /// </summary>
    [JsonExtensionData]
    public IDictionary<string, object> AdditionalProperties { get; set; } = new Dictionary<string, object>();

    /// <summary>
    /// Initializes a new instance of the <see cref="TavilySearchRequest" /> class.
    /// </summary>
    public TavilySearchRequest(
        string query,
        string? topic,
        string? timeRange,
        int? days,
        string? searchDepth,
        int? chunksPerSource,
        bool? includeImages,
        bool? includeImageDescriptions,
        bool? includeAnswer,
        bool? includeRawContent,
        int? maxResults,
        IList<string>? includeDomains,
        IList<string>? excludeDomains,
        string? country = null,
        string? startDate = null,
        string? endDate = null,
        bool? safeSearch = null,
        string? includeDomainsMode = null,
        string? language = null,
        bool? filterByLanguage = null,
        bool? exactMatch = null,
        bool? autoParameters = null)
    {
        this.Query = query ?? throw new ArgumentNullException(nameof(query));
        this.Topic = topic;
        this.TimeRange = timeRange;
        this.Days = days;
        this.SearchDepth = searchDepth;
        this.ChunksPerSource = chunksPerSource;
        this.IncludeImages = includeImages;
        this.IncludeImageDescriptions = includeImageDescriptions;
        this.IncludeAnswer = includeAnswer;
        this.IncludeRawContent = includeRawContent;
        this.MaxResults = maxResults;
        this.IncludeDomains = includeDomains;
        this.ExcludeDomains = excludeDomains;
        this.Country = country;
        this.StartDate = startDate;
        this.EndDate = endDate;
        this.SafeSearch = safeSearch;
        this.IncludeDomainsMode = includeDomainsMode;
        this.Language = language;
        this.FilterByLanguage = filterByLanguage;
        this.ExactMatch = exactMatch;
        this.AutoParameters = autoParameters;
    }
}
