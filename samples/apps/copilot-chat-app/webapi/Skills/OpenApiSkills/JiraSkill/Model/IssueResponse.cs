// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

public class IssueResponse
{
    /// <summary>
    /// Gets or sets the ID of the label.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Gets or sets the name of the label.
    /// </summary>
    [JsonPropertyName("key")]
    public string key { get; set; }

    /// <summary>
    /// Gets or sets the description of the label.
    /// </summary>
    [JsonPropertyName("self")]
    public string self { get; set; }

    [JsonPropertyName("fields")]
    public Fields fields { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="IssueResponse"/> class.
    /// </summary>
    /// <param name="id">The GUID of the Issue.</param>
    /// <param name="key">The readable id of the Issue.</param>
    /// <param name="self">The url of the Issue.</param>
    /// <param name="fields">The fields that make up the response body.</param>
    public IssueResponse(string id, string key, string self, Fields fields)
    {
        this.Id = id;
        this.key = key;
        this.self = self;
        this.fields = fields;
    }
}
