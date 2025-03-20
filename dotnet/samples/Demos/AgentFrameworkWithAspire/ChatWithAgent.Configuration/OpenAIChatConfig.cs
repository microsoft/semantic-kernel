// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ChatWithAgent.Configuration;

/// <summary>
/// OpenAI chat configuration.
/// </summary>
public sealed class OpenAIChatConfig
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string ConfigSectionName = "OpenAIChat";

    /// <summary>
    /// The name of the chat model.
    /// </summary>
    [Required]
    public string ModelName { get; set; } = string.Empty;
}
