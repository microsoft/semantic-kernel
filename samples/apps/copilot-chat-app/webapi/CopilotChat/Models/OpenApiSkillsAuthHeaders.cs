// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;

namespace SemanticKernel.Service.CopilotChat.Models;

/// /// <summary>
/// Represents the authentication headers for imported OpenAPI Plugin Skills.
/// </summary>
public class OpenApiSkillsAuthHeaders
{
    /// <summary>
    /// Gets or sets the MS Graph authentication header value.
    /// </summary>
    [FromHeader(Name = "x-sk-copilot-graph-auth")]
    public string? GraphAuthentication { get; set; }

    /// <summary>
    /// Gets or sets the Jira authentication header value.
    /// </summary>
    [FromHeader(Name = "x-sk-copilot-jira-auth")]
    public string? JiraAuthentication { get; set; }

    /// <summary>
    /// Gets or sets the GitHub authentication header value.
    /// </summary>
    [FromHeader(Name = "x-sk-copilot-github-auth")]
    public string? GithubAuthentication { get; set; }

    /// <summary>
    /// Gets or sets the Klarna header value.
    /// </summary>
    [FromHeader(Name = "x-sk-copilot-klarna-auth")]
    public string? KlarnaAuthentication { get; set; }
}
