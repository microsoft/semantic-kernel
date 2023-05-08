// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SharpYaml.Tokens;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

public class CommentResponse
{
    /// <summary>
    /// Gets or sets the list of all comments contained in this comment response.
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
