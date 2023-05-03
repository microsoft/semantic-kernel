using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills;

/// <summary>
/// Represents a GitHub Pull Request.
/// </summary>
public class PullRequest
{
    // The URL of the pull request
    [JsonPropertyName("url")]
    public System.Uri Url { get; set; }

    // The unique identifier of the pull request
    [JsonPropertyName("id")]
    public int Id { get; set; }

    // The number of the pull request
    [JsonPropertyName("number")]
    public int Number { get; set; }

    // The state of the pull request
    [JsonPropertyName("state")]
    public string State { get; set; }

    // Whether the pull request is locked
    [JsonPropertyName("locked")]
    public bool Locked { get; set; }

    // The title of the pull request
    [JsonPropertyName("title")]
    public string Title { get; set; }

    // The user who created the pull request
    [JsonPropertyName("user")]
    public GitHubUser User { get; set; }

    // The labels associated with the pull request
    [JsonPropertyName("labels")]
    public List<Label> Labels { get; set; }

    // The date and time when the pull request was last updated
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }

    // The date and time when the pull request was closed
    [JsonPropertyName("closed_at")]
    public DateTime? ClosedAt { get; set; }

    // The date and time when the pull request was merged
    [JsonPropertyName("merged_at")]
    public DateTime? MergedAt { get; set; }

    // Constructor
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
