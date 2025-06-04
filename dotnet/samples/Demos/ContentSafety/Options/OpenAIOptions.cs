// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Options;

/// <summary>
/// Configuration for OpenAI chat completion service.
/// </summary>
public class OpenAIOptions
{
    public const string SectionName = "OpenAI";

    [Required]
    public string ChatModelId { get; set; }

    [Required]
    public string ApiKey { get; set; }
}
