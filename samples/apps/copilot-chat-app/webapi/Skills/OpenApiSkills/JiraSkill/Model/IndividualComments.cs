// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

public class IndividualComments
{
    /// <summary>
    /// Gets or sets the body of the comment.
    /// </summary>
    [JsonPropertyName("body")]
    public string body { get; set; }

    /// <summary>
    /// Gets or sets the author name.
    /// </summary>
    [JsonPropertyName("author")]
    public CommentAuthor author { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="IndividualComments"/> class.
    /// </summary>
    /// <param name="body">List of all comments on the Issue.</param>
    /// <param name="author">Author of the comment.</param>
    public IndividualComments(string body, CommentAuthor author)
    {
        this.body = body;
        this.author = author;
    }
}
