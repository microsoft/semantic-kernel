// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// Represents a search response from Keenable.
/// </summary>
#pragma warning disable CA1812 // Instantiated by reflection
internal sealed class KeenableSearchResponse
{
    /// <summary>
    /// The search query that was executed.
    /// </summary>
    [JsonPropertyName("query")]
    public string? Query { get; set; }

    /// <summary>
    /// The list of search results, ranked by relevance.
    /// </summary>
    [JsonPropertyName("results")]
    public IList<KeenableSearchResult> Results { get; set; } = [];
}
#pragma warning restore CA1812 // Instantiated by reflection
