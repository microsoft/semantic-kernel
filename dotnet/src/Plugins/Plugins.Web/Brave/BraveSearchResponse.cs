// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

#pragma warning disable CA1812 // Instantiated by reflection
/// <summary>
/// Brave search response.
/// </summary>
public sealed class BraveSearchResponse<T>
{
    /// <summary>
    /// The type of web search API result. The value is always `search`.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The query string that Brave used for the request.
    /// </summary>
    [JsonPropertyName("query")]
    public BraveQuery? Query { get; set; }

    /// <summary>
    /// Preferred ranked order of search results.
    /// </summary>
    [JsonPropertyName("mixed")]
    public MixedResponse? Mixed { get; set; }

    /// <summary>
    /// News results relevant to the query.
    /// </summary>
    [JsonPropertyName("news")]
    public BraveNews<T>? News { get; set; }
    /// <summary>
    /// Videos relevant to the query return by Brave API.
    /// </summary>
    [JsonPropertyName("videos")]
    public BraveVideos<T>? Videos { get; set; }

    /// <summary>
    /// Web search results relevant to the query return by Brave API.
    /// </summary>
    [JsonPropertyName("web")]
    public BraveWeb<T>? Web { get; set; }
}

/// <summary>
/// A model representing information gathered around the requested query.
/// </summary>
///
public sealed class BraveQuery
{
    /// <summary>
    /// The query string as specified in the request.
    /// </summary>
    [JsonPropertyName("original")]
    public string Original { get; set; } = string.Empty;

    /// <summary>
    /// The query string that Brave used to perform the query. Brave uses the altered query string if the original query string contained spelling mistakes.
    /// For example, if the query string is saling downwind, the altered query string is sailing downwind.
    /// </summary>
    /// <remarks>
    /// The object includes this field only if the original query string contains a spelling mistake.
    /// </remarks>
    [JsonPropertyName("altered")]
    public string? Altered { get; set; }

    /// <summary>
    /// Whether Safe Search was enabled.
    /// </summary>
    [JsonPropertyName("safesearch")]
    public bool? IsSafeSearchEnable { get; set; }

    /// <summary>
    /// Whether there is more content available for query, but the response was restricted due to safesearch.
    /// </summary>
    [JsonPropertyName("show_strict_warning")]
    public bool? ShowStrictWarning { get; set; }

    /// <summary>
    /// Whether the query is a navigational query to a domain.
    /// </summary>
    [JsonPropertyName("is_navigational")]
    public bool? IsNavigational { get; set; }

    /// <summary>
    /// The index of the location .
    /// </summary>
    [JsonPropertyName("local_locations_idx")]
    public int? LocalLocationsIdx { get; set; }

    /// <summary>
    /// Whether the query is trending.
    /// </summary>
    [JsonPropertyName("is_trending")]
    public bool? IsTrending { get; set; }

    /// <summary>
    /// Whether the query has news breaking articles relevant to it.
    /// </summary>
    [JsonPropertyName("is_news_breaking")]
    public bool? IsNewsBreaking { get; set; }

    /// <summary>
    /// Whether the spellchecker was off.
    /// </summary>
    [JsonPropertyName("spellcheck_off")]
    public bool? SpellcheckOff { get; set; }

    /// <summary>
    /// The country that was used.
    /// </summary>
    [JsonPropertyName("country")]
    public string? Country { get; set; }

    /// <summary>
    /// Whether there are bad results for the query.
    /// </summary>
    [JsonPropertyName("bad_results")]
    public bool? BadResults { get; set; }

    /// <summary>
    /// Whether the query should use a fallback.
    /// </summary>
    [JsonPropertyName("should_fallback")]
    public bool? ShouldFallback { get; set; }

    /// <summary>
    /// The gathered postal code associated with the query.
    /// </summary>
    [JsonPropertyName("postal_code")]
    public string? PostalCode { get; set; }

    /// <summary>
    /// The gathered city associated with the query.
    /// </summary>
    [JsonPropertyName("city")]
    public string? City { get; set; }

    /// <summary>
    /// The gathered state associated with the query.
    /// </summary>
    [JsonPropertyName("state")]
    public string? State { get; set; }

    /// <summary>
    /// The country for the request origination.
    /// </summary>
    [JsonPropertyName("header_country")]
    public string? HeaderCountry { get; set; }

    /// <summary>
    /// Whether more results are available for the given query.
    /// </summary>
    [JsonPropertyName("more_results_available")]
    public bool? MoreResultsAvailable { get; set; }

    /// <summary>
    /// Any reddit cluster associated with the query.
    /// </summary>
    [JsonPropertyName("reddit_cluster")]
    public string? RedditCluster { get; set; }
}

/// <summary>
/// A model representing a video result.
/// </summary>
/// <typeparam name="T"></typeparam>
public sealed class BraveVideos<T>
{
    /// <summary>
    /// The type identifying the video result.
    /// </summary>
    /// <remarks>Value is always 'video_result'</remarks>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// A list of video results
    /// </summary>
    [JsonPropertyName("results")]
    public IList<T> Results { get; set; } = [];

    /// <summary>
    /// Whether the video results are changed by a Goggle.
    /// </summary>
    [JsonPropertyName("mutated_by_goggles")]
    public bool? MutatedByGoggles { get; set; }
}

/// <summary>
/// A model representing video results.
/// </summary>
public sealed class BraveVideo
{
    /// <summary>
    /// A time string representing the duration of the video.
    /// </summary>
    /// <remarks>The format can be HH:MM:SS or MM:SS.</remarks>
    [JsonPropertyName("duration")]
    public string Duration { get; set; } = string.Empty;

    /// <summary>
    /// The number of views of the video.
    /// </summary>
    [JsonPropertyName("views")]
    public int? Views { get; set; }

    /// <summary>
    /// The creator of the video.
    /// </summary>
    [JsonPropertyName("creator")]
    public string? Creator { get; set; }

    /// <summary>
    /// The publisher of the video.
    /// </summary>
    [JsonPropertyName("publisher")]
    public string? Publisher { get; set; }

    /// <summary>
    ///A thumbnail associated with the video.
    /// </summary>
    [JsonPropertyName("thumbnail")]
    public Thumbnail? Thumbnail { get; set; }

    /// <summary>
    ///A list of tags associated with the video.
    /// </summary>
    [JsonPropertyName("tags")]
    public IList<string>? Tags { get; set; }

    /// <summary>
    ///Author of the video.
    /// </summary>
    [JsonPropertyName("author")]
    public BraveProfile? AuthorProfile { get; set; }

    /// <summary>
    /// Whether the video requires a subscription to watch.
    /// </summary>
    [JsonPropertyName("requires_subscription")]
    public bool? RequireSubscription { get; set; }
}

/// <summary>
/// A model representing a collection of web search results.
/// </summary>
public sealed class BraveWeb<T>
{
    /// <summary>
    /// A type identifying web search results. The value is always search.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// A list of search results.
    /// </summary>
    [JsonPropertyName("results")]
    public IList<T> Results { get; set; } = [];

    /// <summary>
    /// Whether the results are family friendly.
    /// </summary>
    [JsonPropertyName("family_friendly")]
    public bool? FamilyFriendly { get; set; }
}

/// <summary>
/// A model representing news results.
/// </summary>
public sealed class BraveNews<T>
{
    /// <summary>
    /// The type representing the news. The value is always news.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// A list of news results.
    /// </summary>
    [JsonPropertyName("results")]
    public IList<T> Results { get; set; } = [];

    /// <summary>
    /// Whether the news results are changed by a Goggle. False by default
    /// </summary>
    [JsonPropertyName("mutated_by_googles")]
    public bool? MutatedByGoogles { get; set; }
}

/// <summary>
/// A result which can be used as a button.
/// </summary>
public sealed class Button
{
    /// <summary>
    /// A result which can be used as a button.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The title of the result.
    /// </summary>
    [JsonPropertyName("title")]
    public string? Title { get; set; }

    /// <summary>
    /// The url for the button result.
    /// </summary>
    [JsonPropertyName("url")]
#pragma warning disable CA1056
    public string? Url { get; set; }
#pragma warning restore CA1056
}

/// <summary>
/// Aggregated deep results from news, social, videos and images.
/// </summary>
public sealed class DeepResults
{
    /// <summary>
    /// A list of buttoned results associated with the result.
    /// </summary>
    [JsonPropertyName("buttons")]
    public List<Button>? Buttons { get; set; }
}

/// <summary>
/// The ranking order of results on a search result page.
/// </summary>
public sealed class ResultReference
{
    /// <summary>
    /// The type of the result.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The 0th based index where the result should be placed.
    /// </summary>
    [JsonPropertyName("index")]
    public int? Index { get; set; }

    /// <summary>
    /// Whether to put all the results from the type at specific position.
    /// </summary>
    [JsonPropertyName("all")]
    public bool? All { get; set; }
}

/// <summary>
/// Aggregated information about a url.
/// </summary>
public sealed class MetaUrl
{
    /// <summary>
    /// The protocol scheme extracted from the url.
    /// </summary>
    [JsonPropertyName("scheme")]
    public string Scheme { get; set; } = string.Empty;

    /// <summary>
    /// The network location part extracted from the url.
    /// </summary>
    [JsonPropertyName("netloc")]
    public string Netloc { get; set; } = string.Empty;

    /// <summary>
    /// The lowercased domain name extracted from the url.
    /// </summary>
    [JsonPropertyName("hostname")]
    public string? Hostname { get; set; }

    /// <summary>
    /// The favicon used for the url.
    /// </summary>
    [JsonPropertyName("favicon")]
    public string? Favicon { get; set; }

    /// <summary>
    /// The hierarchical path of the url useful as a display string.
    /// </summary>
    [JsonPropertyName("path")]
    public string? Path { get; set; }
}

/// <summary>
/// The ranking order of results on a search result page.
/// </summary>
public sealed class MixedResponse
{
    /// <summary>
    /// The type representing the model mixed. The value is always mixed.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The ranking order for the main section of the search result page.
    /// </summary>
    [JsonPropertyName("main")]
    public List<ResultReference>? Main { get; set; }

    /// <summary>
    /// The ranking order for the top section of the search result page.
    /// </summary>
    [JsonPropertyName("top")]
    public List<ResultReference>? Top { get; set; }

    /// <summary>
    /// The ranking order for the side section of the search result page.
    /// </summary>
    [JsonPropertyName("side")]
    public List<ResultReference>? Side { get; set; }
}

/// <summary>
/// A profile of an entity.
/// </summary>
public sealed class BraveProfile
{
    /// <summary>
    /// The name of the profile.
    /// </summary>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>
    /// The long name of the profile.
    /// </summary>
    [JsonPropertyName("url")]
#pragma warning disable CA1056
    public string? Url { get; set; }
#pragma warning restore CA1056

    /// <summary>
    /// The original url where the profile is available.
    /// </summary>
    [JsonPropertyName("long_name")]
    public string? LongName { get; set; }

    /// <summary>
    /// The original url where the profile is available.
    /// </summary>
    [JsonPropertyName("img")]
    public string? Img { get; set; }
}

/// <summary>
/// Aggregated details representing a picture thumbnail.
/// </summary>
public sealed class Thumbnail
{
    /// <summary>
    /// The served url of the picture thumbnail.
    /// </summary>
    [JsonPropertyName("src")]
    public string? Src { get; set; }

    /// <summary>
    /// The served url of the picture thumbnail
    /// </summary>
    [JsonPropertyName("original")]
    public string? Original { get; set; }

    /// <summary>
    /// Is the ThumbNail is a Logo or not
    /// </summary>
    [JsonPropertyName("logo")]
    public bool? Logo { get; set; }
}
