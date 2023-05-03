using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills.OpenApiSkills;

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
        Name = name;
        FullName = fullName;
    }

}