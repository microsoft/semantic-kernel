// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace GitHubPlugin.Model;

/// <summary>
/// Represents a user on GitHub.
/// </summary>
public class GitHubUser
{
    /// <summary>
    /// The user's name.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The user's email address.
    /// </summary>
    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;
}
