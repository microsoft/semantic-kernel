// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
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
                Size = 10,
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
