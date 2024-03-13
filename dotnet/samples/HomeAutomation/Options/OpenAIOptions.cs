// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace HomeAutomation.Options;

/// <summary>
/// OpenAI settings.
/// </summary>
public sealed class OpenAIOptions
{
    [Required]
    public string ChatModelId { get; set; } = string.Empty;

    [Required]
    public string ApiKey { get; set; } = string.Empty;
}
