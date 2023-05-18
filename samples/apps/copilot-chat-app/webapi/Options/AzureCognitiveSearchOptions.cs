// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration settings for connecting to Azure Cognitive Search.
/// </summary>
public class AzureCognitiveSearchOptions
{
    /// <summary>
    /// Gets or sets the endpoint protocol and host (e.g. https://contoso.search.windows.net).
    /// </summary>
    [Required, Url]
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Key to access Azure Cognitive Search.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;
}
