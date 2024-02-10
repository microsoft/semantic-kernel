// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace HomeAutomation.Options;

/// <summary>
/// Loads configuration upon instantiation.
/// </summary>
public sealed class AzureOpenAiOptions
{
    [Required]
    public string Deployment { get; set; } = string.Empty;

    [Required]
    public string Endpoint { get; set; } = string.Empty;

    [Required]
    public string ApiKey { get; set; } = string.Empty;
}
