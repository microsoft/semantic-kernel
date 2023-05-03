using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills;

/// <summary>
/// Represents a GitHub Repo.
/// </summary>
public class Repo
{
    // The name of the repo
    [JsonPropertyName("name")]
    public string Name { get; set; }

    // The full name of the repo
    [JsonPropertyName("full_name")]
    public string FullName { get; set; }

    public Repo(string name, string fullName)
    {
        this.Name = name;
        this.FullName = fullName;
    }

}
