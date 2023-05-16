// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

/// <summary>
/// Represents a the list of comments that make up a CommentResponse.
/// </summary>
public class CommentResponse
{
    /// <summary>
    /// Gets or sets the list of all comments contained in this comment response.
    /// </summary>
    [JsonPropertyName("comments")]
    public IEnumerable<IndividualComments> AllComments { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CommentResponse"/> class.
    /// </summary>
    /// <param name="allComments">List of all comments on the Issue.</param>
    public CommentResponse(IEnumerable<IndividualComments> allComments)
    {
        this.AllComments = allComments;
    }
}
