// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

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
}
