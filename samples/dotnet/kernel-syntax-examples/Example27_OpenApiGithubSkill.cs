// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Skills;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RepoUtils;

public class PullRequest
{
    public string? number { get; set; }

}

public class PullRequests
{
    public List<PullRequests>? content { get; set; }
}

/// <summary>
/// Import and run GitHub Functions using OpenAPI Skill.
/// To use this example, run:
/// dotnet user-secrets set "GITHUB_PERSONAL_ACCESS_TOKEN" "github_pat_..."
/// Make sure your GitHub PAT has read permissions set for Pull Requests.
/// Creating a PAT: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
/// </summary>
/// <returns></returns>
public static class Example27_OpenApiGitHubSkill
{
    public static async Task RunAsync()
    {
        var authenticationProvider = new BearerAuthenticationProvider(() => getToken());
        Console.WriteLine("Example27_OpenApiGitHubSkill");
        var firstPRNumber = await ListPullRequestsFromGitHubAsync(authenticationProvider);
        await GetPullRequestFromGitHubAsync(authenticationProvider, firstPRNumber);
    }

    private static Task<string> getToken()
    {
        return Task.FromResult(Env.Var("GITHUB_PERSONAL_ACCESS_TOKEN"));
    }

    public static async Task<string> ListPullRequestsFromGitHubAsync(BearerAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        var skill = await kernel.ImportOpenApiSkillFromResourceAsync(SkillResourceNames.GitHub,
            authenticationProvider.AuthenticateRequestAsync);

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");

        // Run
        var result = await kernel.RunAsync(contextVariables, skill["ListPulls"]);

        Console.WriteLine("Successful GitHub List Pull Requests skill response.");
        var resultJson = JsonConvert.DeserializeObject<Dictionary<string, object>>(result.Result);
        var pullRequests = JArray.Parse((string)resultJson!["content"]);

        if (pullRequests != null && pullRequests.First != null)
        {
            var number = pullRequests.First["number"];
            return number?.ToString() ?? "-1";
        }
        else
        {
            return "-1";
        }
    }

    public static async Task GetPullRequestFromGitHubAsync(BearerAuthenticationProvider authenticationProvider, string pullNumber)
    {
        var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        var skill = await kernel.ImportOpenApiSkillFromResourceAsync(SkillResourceNames.GitHub,
            authenticationProvider.AuthenticateRequestAsync);

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");
        contextVariables.Set("pull_number", pullNumber);

        // Run
        var result = await kernel.RunAsync(contextVariables, skill["GetPull"]);

        Console.WriteLine("Successful GitHub Get Pull Request skill response: {0}", result);
    }
}
