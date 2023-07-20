// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for content moderation.
/// </summary>
public class ContentModerationOptions
{
    public const string PropertyName = "ContentModeration";

    /// <summary>
    /// Whether to enable content moderation.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public bool Enabled { get; set; } = false;

    /// <summary>
    /// Azure Content Moderator endpoints
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Key to access the content moderation service.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;

    /// <summary>
    /// Set the violation threshold. See https://github.com/Azure/Project-Carnegie-Private-Preview for details.
    /// </summary>
    [Range(0, int.MaxValue)]
    public short ViolationThreshold { get; set; } = 4;
}
