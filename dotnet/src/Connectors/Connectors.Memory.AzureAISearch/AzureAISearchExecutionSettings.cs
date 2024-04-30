// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Azure.Search.Documents;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Search;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Provides execution settings for a search request.
/// </summary>
public class AzureAISearchExecutionSettings : SearchExecutionSettings
{
    /// <summary>
    /// Name of the field that contains the name to return.
    /// </summary>
    [JsonPropertyName("name_field")]
    public string? NameField { get; set; }

    /// <summary>
    /// Name of the field that contains the snippet of text to return.
    /// </summary>
    [JsonPropertyName("snippet_field")]
    public string? SnippetField { get; set; }

    /// <summary>
    /// Name of the field that contains the link to return.
    /// </summary>
    [JsonPropertyName("link_field")]
    public string? LinkField { get; set; }

    /// <summary>
    /// Parameters for filtering, sorting, faceting, paging, and other search query behaviors.
    /// </summary>
    public SearchOptions? SearchOptions
    {
        get
        {
            this._searchOptions ??= new SearchOptions()
            {
                QueryType = SearchQueryType.Simple,
                IncludeTotalCount = true,
                Size = this.Count,
                Skip = this.Offset,
            };
            return this._searchOptions;
        }
        set
        {
            this._searchOptions = value;
        }
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <returns>An instance of <see cref="AzureAISearchExecutionSettings" /></returns>
    public static AzureAISearchExecutionSettings FromExecutionSettings(SearchExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new AzureAISearchExecutionSettings();
        }

        if (executionSettings is AzureAISearchExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var azureExecutionSettings = JsonSerializer.Deserialize<AzureAISearchExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (azureExecutionSettings is not null)
        {
            return azureExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(AzureAISearchExecutionSettings)}", nameof(executionSettings));
    }

    private SearchOptions? _searchOptions;
}
