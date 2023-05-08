// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;

public class IssueResponse
{
    /// <summary>
    /// Gets or sets the GUID of the issue.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Gets or sets the issue key, which is a readable id different from the GUID above.
    /// </summary>
    [JsonPropertyName("key")]
    public string key { get; set; }

    /// <summary>
    /// Gets or sets the url of the issue.
    /// </summary>
    [JsonPropertyName("self")]
    public string self { get; set; }

    /// <summary>
    /// Gets or sets the Fields describing the IssueResponse.
    /// </summary>
    [JsonPropertyName("fields")]
    public IssueResponseFields fields { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="IssueResponse"/> class.
    /// </summary>
    /// <param name="id">The GUID of the Issue.</param>
    /// <param name="key">The readable id of the Issue.</param>
    /// <param name="self">The url of the Issue.</param>
    /// <param name="fields">The fields that make up the response body.</param>
    public IssueResponse(string id, string key, string self, IssueResponseFields fields)
    {
        this.Id = id;
        this.key = key;
        this.self = self;
        this.fields = fields;
    }
}
