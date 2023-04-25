using Microsoft.AspNetCore.Mvc;

namespace SemanticKernel.Service.Plugins;

public class PluginAuthHeaders
{
    [FromHeader(Name = "x-sk-copilot-graph-authorization")]
    public string? GraphAuthentication { get; set; }

    [FromHeader(Name = "x-sk-copilot-jira-authorization")]
    public string? JiraAuthentication { get; set; }

    [FromHeader(Name = "x-sk-copilot-github-authorization")]
    public string? GithubAuthentication { get; set; }
}
