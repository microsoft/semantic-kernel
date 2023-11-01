// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// A sealed class containing the deserialized response from the Bing Search API.
/// </summary>
/// <returns>A WebPage object containing the Bing Search API response data.</returns>
/// <remarks><b>Note:</b> Complex types are not compatible with the kernel for chaining yet. See <see href="https://github.com/microsoft/semantic-kernel/pull/2053#discussion_r1274782835">PR#2053</see></remarks>
[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Class is instantiated through deserialization."),
    SuppressMessage("Performance", "CA1056:Change the type of parameter 'uri'...",
    Justification = "A constant Uri cannot be defined, as required by this class")]
public sealed class WebPage
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("url")]
    public string Url { get; set; } = string.Empty;

    [JsonPropertyName("snippet")]
    public string Snippet { get; set; } = string.Empty;
}

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
public sealed class WebSearchResponse
{
    [JsonPropertyName("webPages")]
    public WebPages? WebPages { get; set; }
}

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Class is instantiated through deserialization.")]
public sealed class WebPages
{
    [JsonPropertyName("value")]
    public WebPage[]? Value { get; set; }
}
