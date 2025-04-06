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
    /// Whether the query has location relevance .
    /// </summary>
    [JsonPropertyName("is_geolocal")]
    public bool? IsGeolocal { get; set; }

    /// <summary>
    /// Whether the query was decided to be location sensitive.
    /// </summary>
    [JsonPropertyName("local_decision")]
    public string? LocalDecision { get; set; }

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
    /// Whether the query requires location information for better results.
    /// </summary>
    [JsonPropertyName("ask_for_location")]
    public bool? AskForLocation { get; set; }

    // Language

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
    /// The gathered location latitutde associated with the query.
    /// </summary>
    [JsonPropertyName("lat")]
    public string? Lat { get; set; }

    /// <summary>
    ///The gathered location longitude associated with the query.
    /// </summary>
    [JsonPropertyName("long")]
    public string? Longa { get; set; }

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
    /// Any custom location labels attached to the query.
    /// </summary>
    [JsonPropertyName("custom_location_label")]
    public string? CustomLocationLabel { get; set; }

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
    public IList<T>? Results { get; set; }

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

/// <summary>
/// A result that is location relevant.
/// </summary>
public sealed class LocationResult
{
    /// <summary>
    /// Location result type identifier. The value is always location_result.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// A Temporary id associated with this result, which can be used to retrieve extra information about the location. It remains valid for 8 hours…
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The complete url of the provider.
    /// </summary>
    [JsonPropertyName("provider_url")]
#pragma warning disable CA1056
    public string? ProviderUrl { get; set; }
#pragma warning restore CA1056

    /// <summary>
    /// A list of coordinates associated with the location. This is a lat long represented as a floating point.
    /// </summary>
    [JsonPropertyName("coordinates")]
    public List<float>? Coordinates { get; set; }

    /// <summary>
    /// The zoom level on the map.
    /// </summary>
    [JsonPropertyName("zoom_level")]
    public int? ZoomLevel { get; set; }

    /// <summary>
    /// The thumbnail associated with the location.
    /// </summary>
    [JsonPropertyName("thumbnail")]
    public Thumbnail? Thumbnail { get; set; }

    /// <summary>
    /// The postal address associated with the location.
    /// </summary>
    [JsonPropertyName("postal_address")]
    public PostalAddress? PostalAddress { get; set; }

    /// <summary>
    /// The opening hours, if it is a business, associated with the location .
    /// </summary>
    [JsonPropertyName("opening_hours")]
    public OpeningHours? OpeningHours { get; set; }

    /// <summary>
    /// The contact of the business associated with the location.
    /// </summary>
    [JsonPropertyName("contact")]
    public Contact? Contact { get; set; }

    /// <summary>
    /// A display string used to show the price classification for the business.
    /// </summary>
    [JsonPropertyName("price_range")]
    public string? PriceRange { get; set; }

    /// <summary>
    ///  The ratings of the business.
    /// </summary>
    [JsonPropertyName("rating")]
    public Rating? Rating { get; set; }

    /// <summary>
    /// The distance of the location from the client.
    /// </summary>
    [JsonPropertyName("distance")]
    public Unit? Distance { get; set; }

    /// <summary>
    /// Profiles associated with the business.
    /// </summary>
    [JsonPropertyName("profiles")]
    public List<DataProvider>? Profiles { get; set; }

    /// <summary>
    /// Aggregated reviews from various sources relevant to the business.
    /// </summary>
    [JsonPropertyName("reviews")]
    public Reviews? Reviews { get; set; }

    /// <summary>
    /// A bunch of pictures associated with the business.
    /// </summary>
    [JsonPropertyName("pictures")]
    public PictureResults? Pictures { get; set; }

    /// <summary>
    /// /An action to be taken.
    /// </summary>
    [JsonPropertyName("action")]
    public Action? Action { get; set; }

    /// <summary>
    /// A list of cuisine categories served.
    /// </summary>
    [JsonPropertyName("serves_cuisine")]
    public List<string>? ServesCuisine { get; set; }

    /// <summary>
    /// A list of categories.
    /// </summary>
    [JsonPropertyName("categories")]
    public List<string>? Categories { get; set; }

    /// <summary>
    /// An icon category.
    /// </summary>
    [JsonPropertyName("icon_category")]
    public string? IconCategory { get; set; }

    /// <summary>
    /// Web results related to this location.
    /// </summary>
    [JsonPropertyName("results")]
    public LocationWebResult? Results { get; set; }

    /// <summary>
    /// IANA timezone identifier.
    /// </summary>
    [JsonPropertyName("timezone")]
    public string? Timezone { get; set; }

    /// <summary>
    /// The utc offset of the timezone.
    /// </summary>
    [JsonPropertyName("timezone_offset")]
    public string? TimezoneOffset { get; set; }
}

/// <summary>
/// A model representing a web result related to a location
/// </summary>
public sealed class LocationWebResult
{
    /// <summary>
    /// 	Aggregated information about the url.
    /// </summary>
    public MetaUrl? MetaUrl { get; set; }
}

/// <summary>
/// A model representing a postal address of a location
/// </summary>
public sealed class PostalAddress
{
    /// <summary>
    ///The type identifying a postal address. The value is always PostalAddress.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; } = string.Empty;

    /// <summary>
    ///The country associated with the location.
    /// </summary>
    [JsonPropertyName("country")]
    public string? Country { get; set; }

    /// <summary>
    ///The postal code associated with the location.
    /// </summary>
    [JsonPropertyName("postalCode")]
    public string? PostalCode { get; set; }

    /// <summary>
    ///The street address associated with the location.
    /// </summary>
    [JsonPropertyName("streetAddress")]
    public string? StreetAddress { get; set; }

    /// <summary>
    ///The region associated with the location. This is usually a state.
    /// </summary>
    [JsonPropertyName("addressRegion")]
    public string? AddressRegion { get; set; }

    /// <summary>
    /// The address locality or subregion associated with the location.
    /// </summary>
    [JsonPropertyName("addressLocality")]
    public string? AddressLocality { get; set; }

    /// <summary>
    ///The displayed address string.
    /// </summary>
    [JsonPropertyName("displayAddress")]
    public string? DisplayAddress { get; set; }
}

/// <summary>
///Opening hours of a business at a particular location.
/// </summary>
public sealed class OpeningHours
{
    /// <summary>
    ///The current day opening hours. Can have two sets of opening hours.
    /// </summary>
    [JsonPropertyName("current_day")]
    public List<DayOpeningHours>? CurrentDay { get; set; }

    /// <summary>
    ///The opening hours for the whole week.
    /// </summary>
    [JsonPropertyName("days")]
    public List<List<DayOpeningHours>>? Days { get; set; }
}

/// <summary>
///A model representing the opening hours for a particular day for a business at a particular location.
/// </summary>
public sealed class DayOpeningHours
{
    /// <summary>
    ///A short string representing the day of the week.
    /// </summary>
    [JsonPropertyName("abbr_name")]
    public string? AbbrName { get; set; }

    /// <summary>
    ///A full string representing the day of the week.
    /// </summary>
    [JsonPropertyName("full_name")]
    public string? FullName { get; set; }

    /// <summary>
    ///A 24 hr clock time string for the opening time of the business on a particular day.
    /// </summary>
    [JsonPropertyName("opens")]
    public string? Opens { get; set; }

    /// <summary>
    ///A 24 hr clock time string for the closing time of the business on a particular day.
    /// </summary>
    [JsonPropertyName("closes")]
    public string? Closes { get; set; }
}

/// <summary>
///A model representing contact information for an entity.
/// </summary>
public sealed class Contact
{
    /// <summary>
    ///The email address.
    /// </summary>
    [JsonPropertyName("email")]
    public string? Email { get; set; }

    /// <summary>
    ///The telephone number.
    /// </summary>
    [JsonPropertyName("telephone")]
    public string? Telephone { get; set; }
}

/// <summary>
///The rating associated with an entity.
/// </summary>
public sealed class Rating
{
    /// <summary>
    ///The current value of the rating.
    /// </summary>
    [JsonPropertyName("ratingValue")]
    public float? RatingValue { get; set; }

    /// <summary>
    ///Best rating received.
    /// </summary>
    [JsonPropertyName("bestRating")]
    public float? BestRating { get; set; }

    /// <summary>
    ///The number of reviews associated with the rating.
    /// </summary>
    [JsonPropertyName("reviewCount")]
    public int? ReviewCount { get; set; }

    /// <summary>
    ///The profile associated with the rating.
    /// </summary>
    [JsonPropertyName("profile")]
    public BraveProfile? Profile { get; set; }

    /// <summary>
    ///Whether the rating is coming from Tripadvisor.
    /// </summary>
    [JsonPropertyName("is_tripadvisor")]
    public bool? IsTripAdvisor { get; set; }
}

/// <summary>
///A model representing the data provider associated with the entity.
/// </summary>
public sealed class DataProvider
{
    /// <summary>
    ///The type representing the source of data. This is usually external.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; } = string.Empty;

    /// <summary>
    ///The name of the data provider. This can be a domain.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    ///The url where the information is coming from.
    /// </summary>
    [JsonPropertyName("url")]
#pragma warning disable CA1056
    public string? DataProviderUrl { get; set; }
#pragma warning restore CA1056

    /// <summary>
    ///The long name for the data provider.
    /// </summary>
    [JsonPropertyName("long_name")]
    public string? LongName { get; set; }

    /// <summary>
    ///The served url for the image data.
    /// </summary>
    [JsonPropertyName("img")]
    public string? Img { get; set; }
}

/// <summary>
///The reviews associated with an entity.
/// </summary>
public sealed class Reviews
{
    /// <summary>
    ///A list of trip advisor reviews for the entity.
    /// </summary>
    [JsonPropertyName("results")]
    public List<TripAdvisorReview>? Results { get; set; }

    /// <summary>
    ///An url to a web page where more information on the result can be seen.
    /// </summary>
    [JsonPropertyName("viewMoreUrl")]
#pragma warning disable CA1056
    public string ViewMoreUrl { get; set; } = string.Empty;
#pragma warning restore CA105

    /// <summary>
    ///Any reviews available in a foreign language.
    /// </summary>
    [JsonPropertyName("reviews_in_foreign_language")]
    public bool? ReviewsInForeignLanguage { get; set; }
}

/// <summary>
///A model representing a TripAdvisor review.
/// </summary>
public sealed class TripAdvisorReview
{
    /// <summary>
    ///The title of the review.
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    ///A description seen in the review.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    ///The date when the review was published.
    /// </summary>
    [JsonPropertyName("date")]
    public string Date { get; set; } = string.Empty;

    /// <summary>
    ///A rating given by the reviewer.
    /// </summary>
    [JsonPropertyName("rating")]
    public Rating? Rating { get; set; }

    /// <summary>
    ///The author of the review.
    /// </summary>
    [JsonPropertyName("author")]
    public Person? Author { get; set; }

    /// <summary>
    ///A url link to the page where the review can be found.
    /// </summary>
    [JsonPropertyName("review_url")]
    public string? ReviewUrl { get; set; }

    /// <summary>
    ///The language of the review.
    /// </summary>
    [JsonPropertyName("language")]
    public string? Language { get; set; }
}

/// <summary>
///A model representing a list of pictures.
/// </summary>
public sealed class PictureResults
{
    /// <summary>
    ///A url to view more pictures.
    /// </summary>
    [JsonPropertyName("viewMoreUrl")]
    public string? ViewMoreUrl { get; set; }

    /// <summary>
    ///A list of thumbnail results.
    /// </summary>
    [JsonPropertyName("results")]
    public List<Thumbnail>? Results { get; set; }
}

/// <summary>
/// A model describing a person entity.
/// </summary>
public sealed class Person
{
    /// <summary>
    /// A type identifying a person. The value is always person.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
}

/// <summary>
///A model representing an action to be taken.
/// </summary>
public sealed class Action
{
    /// <summary>
    ///The type representing the action.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    ///A url representing the action to be taken.
    /// </summary>
    [JsonPropertyName("url")]
#pragma warning disable CA1056
    public string ActionUrl { get; set; } = string.Empty;
#pragma warning restore CA1056
}

/// <summary>
///A model representing a unit of measurement.
/// </summary>
public sealed class Unit
{
    /// <summary>
    ///The quantity of the unit.
    /// </summary>
    [JsonPropertyName("value")]
    public float Value { get; set; } = 0.0f;

    /// <summary>
    ///The name of the unit associated with the quantity.
    /// </summary>
    [JsonPropertyName("units")]
    public string Units { get; set; } = string.Empty;
}
