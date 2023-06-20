// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.OpenApiSkills.JiraSkill.Model;

/// <summary>
/// Represents the Author of a comment.
/// </summary>
public class CommentAuthor
{
    /// <summary>
    /// Gets or sets the Comment Author's display name.
    /// </summary>
    [JsonPropertyName("displayName")]
    public string DisplayName { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CommentAuthor"/> class.
    /// </summary>
    /// <param name="displayName">Name of Author</param>
    public CommentAuthor(string displayName)
    {
        this.DisplayName = displayName;
    }
}
