// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace OpenApiPluginsExample;

/// <summary>
/// Configuration options for GitHub plugin.
/// </summary>
public sealed class GitHubPluginOptions
{
    public const string PropertyName = "GitHubPlugin";

    /// <summary>
    /// GitHub API key.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;

    /// <summary>
    /// GitHub organization or account containing <see cref="Repository"/> (e.g., "microsoft").
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Owner { get; set; } = string.Empty;

    /// <summary>
    /// GitHub repository (e.g., "semantic-kernel").
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Repository { get; set; } = string.Empty;
}
