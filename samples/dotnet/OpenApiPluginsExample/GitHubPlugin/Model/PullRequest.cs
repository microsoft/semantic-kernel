// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace GitHubPlugin.Model;

/// <summary>
/// Represents a GitHub Pull Request.
/// </summary>
public class PullRequest
{
    /// <summary>
    /// Gets or sets the URL of the pull request
    /// </summary>
    [JsonPropertyName("url")]
    public Uri? Url { get; set; }

    /// <summary>
    /// Gets or sets the unique identifier of the pull request
    /// </summary>
    [JsonPropertyName("id")]
    public int Id { get; set; }

    /// <summary>
    /// Gets or sets the number of the pull request
    /// </summary>
    [JsonPropertyName("number")]
    public int Number { get; set; }

    /// <summary>
    /// Gets or sets the state of the pull request
    /// </summary>
    [JsonPropertyName("state")]
    public string State { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the title of the pull request
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the user who created the pull request
    /// </summary>
    [JsonPropertyName("user")]
    public GitHubUser? User { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was last updated
    /// </summary>
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was closed
    /// </summary>
    [JsonPropertyName("closed_at")]
    public DateTime? ClosedAt { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was merged
    /// </summary>
    [JsonPropertyName("merged_at")]
    public DateTime? MergedAt { get; set; }
}
