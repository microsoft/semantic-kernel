// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// Options used to construct an instance of <see cref="GoogleTextSearch"/>
/// </summary>
public sealed class GoogleTextSearchOptions
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchStringMapper" /> instance that can map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="string"/>
    /// </summary>
    public ITextSearchStringMapper? StringMapper { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchResultMapper" /> instance that can map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    public ITextSearchResultMapper? ResultMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets the country restriction for search results (e.g., "countryUS", "countryFR").
    /// Applied as a default to every search from this instance.
    /// See <see href="https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list"/>.
    /// </summary>
    public string? CountryRestrict { get; init; }

    /// <summary>
    /// Gets or sets the date restriction for results (e.g., "d[number]" for days, "w[number]" for weeks, "m[number]" for months, "y[number]" for years).
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? DateRestrict { get; init; }

    /// <summary>
    /// Gets or sets the geolocation of the end user, specified as a two-letter country code (e.g., "us", "fr").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? GeoLocation { get; init; }

    /// <summary>
    /// Gets or sets the interface language (host language) of the user interface (e.g., "en", "fr").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? InterfaceLanguage { get; init; }

    /// <summary>
    /// Gets or sets a URL to find pages that link to it.
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? LinkSite { get; init; }

    /// <summary>
    /// Gets or sets the language restriction for search results (e.g., "lang_en", "lang_fr").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? LanguageRestrict { get; init; }

    /// <summary>
    /// Gets or sets the licensing filter for search results (e.g., "cc_publicdomain", "cc_attribute").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? Rights { get; init; }

    /// <summary>
    /// Gets or sets the duplicate content filter ("0" to disable, "1" to enable).
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? DuplicateContentFilter { get; init; }
}
