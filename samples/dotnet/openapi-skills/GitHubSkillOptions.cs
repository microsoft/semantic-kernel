// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace OpenApiSkillsExample;

/// <summary>
/// Configuration options for GitHub skill.
/// </summary>
public sealed class GitHubSkillOptions
{
    public const string PropertyName = "GitHubSkill";

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
