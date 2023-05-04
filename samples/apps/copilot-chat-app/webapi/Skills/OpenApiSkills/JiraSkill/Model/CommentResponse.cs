// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SharpYaml.Tokens;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

public class CommentAuthor
{
    /// <summary>
    /// Gets or sets the ID of the label.
    /// </summary>
    [JsonPropertyName("displayName")]
    public string displayName { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CommentAuthor"/> class.
    /// </summary>
    /// <param name="displayName">Name of Author</param>
    public CommentAuthor(string displayName)
    {
        this.displayName = displayName;
    }
}

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

public class CommentResponse
{
    /// <summary>
    /// Gets or sets the ID of the label.
    /// </summary>
    [JsonPropertyName("comments")]
    public List<IndividualComments> allcomments { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CommentResponse"/> class.
    /// </summary>
    /// <param name="allcomments">List of all comments on the Issue.</param>
    public CommentResponse(List<IndividualComments> allcomments)
    {
        this.allcomments = allcomments;
    }
}
