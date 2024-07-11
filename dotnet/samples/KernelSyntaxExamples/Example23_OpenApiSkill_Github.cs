// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RepoUtils;

/// <summary>
/// Import and run GitHub Functions using OpenAPI Skill.
/// To use this example, run:
/// dotnet user-secrets set "Github.PAT" "github_pat_..."
/// Make sure your GitHub PAT has read permissions set for Pull Requests.
/// Creating a PAT: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example23_OpenApiSkill_GitHub
{
    public static async Task RunAsync()
    {
        var authenticationProvider = new BearerAuthenticationProvider(() => { return Task.FromResult(TestConfiguration.Github.PAT); });
        Console.WriteLine("== Example22_c_OpenApiSkill_GitHub ==");
        var firstPRNumber = await ListPullRequestsFromGitHubAsync(authenticationProvider);
        await GetPullRequestFromGitHubAsync(authenticationProvider, firstPRNumber);
    }

    public static async Task<string> ListPullRequestsFromGitHubAsync(BearerAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var skill = await kernel.ImportAIPluginAsync(
            "GitHubSkill",
            "../../../samples/apps/copilot-chat-app/webapi/Skills/OpenApiSkills/GitHubSkill/openapi.json",
            new OpenApiSkillExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");

        // Run
        var result = await kernel.RunAsync(contextVariables, skill["PullsList"]);

        Console.WriteLine("Successful GitHub List Pull Requests skill response.");
        var resultJson = JsonConvert.DeserializeObject<Dictionary<string, object>>(result.Result);
        var pullRequests = JArray.Parse((string)resultJson!["content"]);

        if (pullRequests != null && pullRequests.First != null)
        {
            var number = pullRequests.First["number"];
            return number?.ToString() ?? string.Empty;
        }

        Console.WriteLine("No pull requests found.");

        return string.Empty;
    }

    public static async Task GetPullRequestFromGitHubAsync(BearerAuthenticationProvider authenticationProvider, string pullNumber)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var skill = await kernel.ImportAIPluginAsync(
            "GitHubSkill",
            "../../../samples/apps/copilot-chat-app/webapi/Skills/OpenApiSkills/GitHubSkill/openapi.json",
            new OpenApiSkillExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");
        contextVariables.Set("pull_number", pullNumber);

        // Run
        var result = await kernel.RunAsync(contextVariables, skill["PullsGet"]);

        Console.WriteLine("Successful GitHub Get Pull Request skill response: {0}", result);
    }
}
