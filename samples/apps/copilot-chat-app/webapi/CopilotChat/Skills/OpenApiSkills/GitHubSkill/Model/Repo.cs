// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.OpenApiSkills.GitHubSkill.Model;

/// <summary>
/// Represents a GitHub Repo.
/// </summary>
public class Repo
{
    /// <summary>
    /// Gets or sets the name of the repo
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; }

    /// <summary>
    /// Gets or sets the full name of the repo
    /// </summary>
    [JsonPropertyName("full_name")]
    public string FullName { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Repo"/>.
    /// </summary>
    /// <param name="name">The name of the repository, e.g. "dotnet/runtime".</param>
    /// <param name="fullName">The full name of the repository, e.g. "Microsoft/dotnet/runtime".</param>
    public Repo(string name, string fullName)
    {
        this.Name = name;
        this.FullName = fullName;
    }
}
