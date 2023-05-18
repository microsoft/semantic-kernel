// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.OpenApiSkills.GitHubSkill.Model;

/// <summary>
/// Represents a GitHub Pull Request.
/// </summary>
public class PullRequest
{
    /// <summary>
    /// Gets or sets the URL of the pull request
    /// </summary>
    [JsonPropertyName("url")]
    public System.Uri Url { get; set; }

    /// <summary>
    /// Gets or sets the unique identifier of the pull request
    /// </summary>
    [JsonPropertyName("id")]
    public int Id { get; set; }

    /// <summary>
    /// Gets or sets the number of the pull request
    /// </summary>
    [JsonPropertyName("number")]
    public int Number { get; set; }

    /// <summary>
    /// Gets or sets the state of the pull request
    /// </summary>
    [JsonPropertyName("state")]
    public string State { get; set; }

    /// <summary>
    /// Whether the pull request is locked
    /// </summary>
    [JsonPropertyName("locked")]
    public bool Locked { get; set; }

    /// <summary>
    /// Gets or sets the title of the pull request
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; }

    /// <summary>
    /// Gets or sets the user who created the pull request
    /// </summary>
    [JsonPropertyName("user")]
    public GitHubUser User { get; set; }

    /// <summary>
    /// Gets or sets the labels associated with the pull request
    /// </summary>
    [JsonPropertyName("labels")]
    public List<Label> Labels { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was last updated
    /// </summary>
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was closed
    /// </summary>
    [JsonPropertyName("closed_at")]
    public DateTime? ClosedAt { get; set; }

    /// <summary>
    /// Gets or sets the date and time when the pull request was merged
    /// </summary>
    [JsonPropertyName("merged_at")]
    public DateTime? MergedAt { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PullRequest"/> class, representing a pull request on GitHub.
    /// </summary>
    /// <param name="url">The URL of the pull request.</param>
    /// <param name="id">The unique identifier of the pull request.</param>
    /// <param name="number">The number of the pull request within the repository.</param>
    /// <param name="state">The state of the pull request, such as "open", "closed", or "merged".</param>
    /// <param name="locked">A value indicating whether the pull request is locked for comments or changes.</param>
    /// <param name="title">The title of the pull request.</param>
    /// <param name="user">The user who created the pull request.</param>
    /// <param name="labels">A list of labels assigned to the pull request.</param>
    /// <param name="updatedAt">The date and time when the pull request was last updated.</param>
    /// <param name="closedAt">The date and time when the pull request was closed, or null if it is not closed.</param>
    /// <param name="mergedAt">The date and time when the pull request was merged, or null if it is not merged.</param>
    public PullRequest(
        System.Uri url,
        int id,
        int number,
        string state,
        bool locked,
        string title,
        GitHubUser user,
        List<Label> labels,
        DateTime updatedAt,
        DateTime? closedAt,
        DateTime? mergedAt
    )
    {
        this.Url = url;
        this.Id = id;
        this.Number = number;
        this.State = state;
        this.Locked = locked;
        this.Title = title;
        this.User = user;
        this.Labels = labels;
        this.UpdatedAt = updatedAt;
        this.ClosedAt = closedAt;
        this.MergedAt = mergedAt;
    }
}
