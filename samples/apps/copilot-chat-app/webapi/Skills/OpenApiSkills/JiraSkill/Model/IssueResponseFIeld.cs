// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

namespace SemanticKernel.Service.Skills.OpenApiSkills;

public class Fields
{
    /// <summary>
    /// Gets or sets the ID of the label.
    /// </summary>
    [JsonPropertyName("statuscategorychangedate")]
    public string statuscategorychangedate { get; set; }

    /// <summary>
    /// Gets or sets the name of the label.
    /// </summary>
    [JsonPropertyName("summary")]
    public string summary { get; set; }

    /// <summary>
    /// Gets or sets the description of the label.
    /// </summary>
    [JsonPropertyName("parent")]
    public IssueResponse parent { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Fields"/> class.
    /// </summary>
    /// <param name="statuscategorychangedate">The date time the issue was last changed.</param>
    /// <param name="summary">The summary of the issue.</param>
    /// <param name="parent">The parent of the issue.</param>
    public Fields(string statuscategorychangedate, string summary, IssueResponse parent)
    {
        this.statuscategorychangedate = statuscategorychangedate;
        this.summary = summary;
        this.parent = parent;
    }
}
