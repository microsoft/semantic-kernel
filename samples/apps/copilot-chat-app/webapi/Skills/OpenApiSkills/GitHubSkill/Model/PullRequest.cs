using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills;

public class PullRequest
{
    // The URL of the pull request
    [JsonPropertyName("url")]
    public string Url { get; set; }

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
        string url,
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
        Url = url;
        Id = id;
        Number = number;
        State = state;
        Locked = locked;
        Title = title;
        User = user;
        Labels = labels;
        UpdatedAt = updatedAt;
        ClosedAt = closedAt;
        MergedAt = mergedAt;
    }
}
