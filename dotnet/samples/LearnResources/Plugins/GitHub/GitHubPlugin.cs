// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Plugins;

internal class GitHubSettings
{
    public string BaseUrl { get; set; } = "https://api.github.com";

    public string Token { get; set; } = string.Empty;
}

internal sealed class GitHubPlugin(GitHubSettings settings)
{
    [KernelFunction]
    public async Task<GitHubModels.User> GetUserProfile()
    {
        using HttpClient client = this.CreateClient();
        JsonDocument response = await MakeRequest(client, $"/user");
        return response.Deserialize<GitHubModels.User>();
    }

    [KernelFunction]
    public async Task<GitHubModels.Repo> GetRepositoryAsync(string organization, string repo)
    {
        using HttpClient client = this.CreateClient();
        JsonDocument response = await MakeRequest(client, $"/repos/{organization}/{repo}");

        return response.Deserialize<GitHubModels.Repo>();
    }

    [KernelFunction]
    public async Task<GitHubModels.Issue[]> GetIssues(
        string organization,
        string repo,
        [Description("default count is 30")]
        int? maxResults = null,
        [Description("open, closed, or all")]
        string state = null,
        string label = null,
        string assignee = null)
    {
        using HttpClient client = this.CreateClient();

        string path = $"/repos/{organization}/{repo}/issues?";
        path = BuildQuery(path, "state", state);
        path = BuildQuery(path, "assignee", assignee);
        path = BuildQuery(path, "labels", label);
        path = BuildQuery(path, "per_page", maxResults?.ToString() ?? string.Empty);

        JsonDocument response = await MakeRequest(client, path);

        return response.Deserialize<GitHubModels.Issue[]>();
    }

    [KernelFunction]
    public async Task<GitHubModels.IssueDetail> GetIssueDetail(string organization, string repo, int issueId)
    {
        using HttpClient client = this.CreateClient();

        string path = $"/repos/{organization}/{repo}/issues/{issueId}";

        JsonDocument response = await MakeRequest(client, path);

        return response.Deserialize<GitHubModels.IssueDetail>();
    }

    private HttpClient CreateClient()
    {
        HttpClient client = new()
        {
            BaseAddress = new Uri(settings.BaseUrl)
        };

        client.DefaultRequestHeaders.Clear();
        client.DefaultRequestHeaders.Add("User-Agent", "request");
        client.DefaultRequestHeaders.Add("Accept", "application/vnd.github+json");
        client.DefaultRequestHeaders.Add("Authorization", $"Bearer {settings.Token}");
        client.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");

        return client;
    }

    private static string BuildQuery(string path, string key, string value)
    {
        if (!string.IsNullOrWhiteSpace(value))
        {
            return $"{path}{key}={value}&";
        }

        return path;
    }

    private static async Task<JsonDocument> MakeRequest(HttpClient client, string path)
    {
        Console.WriteLine($"REQUEST: {path}");
        Console.WriteLine();

        HttpResponseMessage response = await client.GetAsync(path);
        response.EnsureSuccessStatusCode();
        string content = await response.Content.ReadAsStringAsync();
        return JsonDocument.Parse(content);
    }
}
