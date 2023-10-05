// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Orchestration;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using RepoUtils;

/// <summary>
/// Import and run GitHub Functions using OpenAPI Plugin.
/// To use this example, run:
/// dotnet user-secrets set "Github.PAT" "github_pat_..."
/// Make sure your GitHub PAT has read permissions set for Pull Requests.
/// Creating a PAT: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example23_OpenApiPlugin_GitHub
{
    public static async Task RunAsync()
    {
        var authenticationProvider = new BearerAuthenticationProvider(() => { return Task.FromResult(TestConfiguration.Github.PAT); });
        Console.WriteLine("== Example23_OpenApiPlugin_GitHub ==");
        var firstPRNumber = await ListPullRequestsFromGitHubAsync(authenticationProvider);
        await GetPullRequestFromGitHubAsync(authenticationProvider, firstPRNumber);
    }

    public static async Task<string> ListPullRequestsFromGitHubAsync(BearerAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var plugin = await kernel.ImportPluginFunctionsAsync(
            "GitHubPlugin",
            "../../../../../../samples/dotnet/OpenApiPluginsExample/GitHubPlugin/openapi.json",
            new OpenApiFunctionExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["PullList"]);

        Console.WriteLine("Successful GitHub List Pull Requests plugin response.");
        var response = kernelResult.GetValue<RestApiOperationResponse>();
        if (response != null)
        {
            var pullRequests = JArray.Parse(response.Content?.ToString() ?? "null");

            if (pullRequests != null && pullRequests.First != null)
            {
                var number = pullRequests.First["number"];
                return number?.ToString() ?? string.Empty;
            }
        }
        Console.WriteLine("No pull requests found.");

        return string.Empty;
    }

    public static async Task GetPullRequestFromGitHubAsync(BearerAuthenticationProvider authenticationProvider, string pullNumber)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var plugin = await kernel.ImportPluginFunctionsAsync(
            "GitHubPlugin",
            "../../../../../../samples/dotnet/OpenApiPluginsExample/GitHubPlugin/openapi.json",
            new OpenApiFunctionExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("owner", "microsoft");
        contextVariables.Set("repo", "semantic-kernel");
        contextVariables.Set("pull_number", pullNumber);

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["PullsGet"]);

        Console.WriteLine("Successful GitHub Get Pull Request plugin response: {0}", kernelResult.GetValue<RestApiOperationResponse>()?.Content);
    }
}
