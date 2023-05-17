// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.OpenApiSkills.JiraSkill.Model;

/// <summary>
/// Represents an individual comment on an issue in jira.
/// </summary>
public class IndividualComments
{
    /// <summary>
    /// Gets or sets the body of the comment.
    /// </summary>
    [JsonPropertyName("body")]
    public string Body { get; set; }

    /// <summary>
    /// Gets or sets the author name.
    /// </summary>
    [JsonPropertyName("author")]
    public CommentAuthor Author { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="IndividualComments"/> class.
    /// </summary>
    /// <param name="body">The actual content of the comment.</param>
    /// <param name="author">Author of the comment.</param>
    public IndividualComments(string body, CommentAuthor author)
    {
        this.Body = body;
        this.Author = author;
    }
}
