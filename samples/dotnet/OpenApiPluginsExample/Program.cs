// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using GitHubPlugin.Model;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

namespace OpenApiPluginsExample;

/// <summary>
/// The chat example below is meant to demonstrate the use of an OpenAPI-based plugin (e.g., GitHub),
/// a planner (e.g., ActionPlanner) and chat completions to create a conversational experience with
/// additional information from a plugin when needed.
/// </summary>
internal sealed class Program
{
    private static async Task Main(string[] args)
    {
        Console.WriteLine("Welcome to Semantic Kernel OpenAPI Plugins Example!");

        // Load configuration
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "appsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "appsettings.Development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Program>()
            .Build();

        // Initialize logger
        using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
            builder.AddConfiguration(configuration.GetSection("Logging"))
                .AddConsole()
                .AddDebug());

        ILogger logger = loggerFactory.CreateLogger<Program>();

        // Initialize semantic kernel
        AIServiceOptions aiOptions = configuration.GetRequiredSection(AIServiceOptions.PropertyName).Get<AIServiceOptions>()
            ?? throw new InvalidOperationException($"Missing configuration for {AIServiceOptions.PropertyName}.");

        KernelBuilder builder = new KernelBuilder()
            .WithLogger(loggerFactory.CreateLogger<IKernel>());

        switch (aiOptions.Type)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                builder.WithAzureChatCompletionService(aiOptions.Models.Completion, aiOptions.Endpoint, aiOptions.Key);
                break;
            case AIServiceOptions.AIServiceType.OpenAI:
                builder.WithOpenAIChatCompletionService(aiOptions.Models.Completion, aiOptions.Key);
                break;
            default:
                throw new InvalidOperationException($"Unhandled AI service type {aiOptions.Type}");
        }

        var kernel = builder.Build();

        // Register the GitHub plugin using an OpenAPI definition containing only pull request GET operations.
        GitHubPluginOptions gitHubOptions = configuration.GetRequiredSection(GitHubPluginOptions.PropertyName).Get<GitHubPluginOptions>()
            ?? throw new InvalidOperationException($"Missing configuration for {GitHubPluginOptions.PropertyName}.");

        BearerAuthenticationProvider authenticationProvider = new(() => Task.FromResult(gitHubOptions.Key));

        await kernel.ImportAIPluginAsync(
            skillName: "GitHubPlugin",
            filePath: Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "GitHubPlugin/openapi.json"),
            new OpenApiSkillExecutionParameters(authCallback: authenticationProvider.AuthenticateRequestAsync));

        // Use a planner to decide when to call the GitHub plugin. Since we are not chaining operations, use
        // the ActionPlanner which is a simplified planner that will always return a 0 or 1 step plan.
        ActionPlanner planner = new(kernel, logger: logger);

        // Chat loop
        IChatCompletion chatGPT = kernel.GetService<IChatCompletion>();
        OpenAIChatHistory chatHistory = (OpenAIChatHistory)chatGPT.CreateNewChat("You are a helpful, friendly, intelligent assistant that is good at conversation.");
        while (true)
        {
            Console.WriteLine("----------------");
            Console.Write("Input: ");
            string? input = Console.ReadLine();

            if (string.IsNullOrWhiteSpace(input))
            {
                continue;
            }

            // Add GitHub's response, if any, to the chat history.
            int planResultTokenAllowance = (int)(aiOptions.TokenLimit * 0.25); // Allow up to 25% of our token limit to be from GitHub.
            string planResult = await PlanGitHubPluginAsync(gitHubOptions, planner, chatHistory, input, planResultTokenAllowance, logger);
            if (!string.IsNullOrWhiteSpace(planResult))
            {
                chatHistory.AddUserMessage(planResult);
            }

            // Add the user's input to the chat history.
            chatHistory.AddUserMessage(input);

            // Remove earlier messages until we are back within our token limit.
            // (Note this sample does not implement long-term memory)
            int tokenCount = CountTokens(JsonSerializer.Serialize(chatHistory));
            while (tokenCount > aiOptions.TokenLimit)
            {
                chatHistory.Messages.RemoveAt(1);
                tokenCount = CountTokens(JsonSerializer.Serialize(chatHistory));
            }
            Console.WriteLine($"(tokens: {tokenCount})");

            // Send the chat history to the AI for a response.
            string reply = await chatGPT.GenerateMessageAsync(chatHistory);
            chatHistory.AddAssistantMessage(reply);

            Console.WriteLine("----------------");
            Console.WriteLine($"Assistant: {reply}");
        }
    }

    /// <summary>
    /// Run the planner to decide whether to run the GitHub plugin function and add the result to the chat history.
    /// </summary>
    private static async Task<string> PlanGitHubPluginAsync(
        GitHubPluginOptions gitHubOptions, ActionPlanner planner, OpenAIChatHistory chatHistory, string input, int tokenAllowance, ILogger logger)
    {
        // Ask the planner to create a plan based off the user's input. If the plan elicits no steps, continue normally.
        Plan plan = await planner.CreatePlanAsync(input);

        // Make sure the plan's state has the GitHub plugin configuration values.
        plan.State.Set("repo", gitHubOptions.Repository);
        plan.State.Set("owner", gitHubOptions.Owner);

        // Run the plan
        SKContext planContext = await plan.InvokeAsync(logger: logger);
        if (planContext.ErrorOccurred)
        {
            logger.LogError(planContext.LastException!, "Unexpected failure executing plan");
            return string.Empty;
        }
        else if (string.IsNullOrWhiteSpace(planContext.Result))
        {
            return planContext.Result;
        }

        if (!TryExtractJsonFromOpenApiPlanResult(planContext.Result, logger, out string planResult))
        {
            planResult = planContext.Result;
        }

        // GitHub responses can be very lengthy - optimize the output so we don't immediately go beyond token limits.
        return OptimizeGitHubPullRequestResponse(planResult, tokenAllowance);
    }

    /// <summary>
    /// Reduce the size of GitHub PullRequest responses.
    /// </summary>
    private static string OptimizeGitHubPullRequestResponse(string planResult, int tokenAllowance)
    {
        string result;
        List<PullRequest> pullRequests = new();
        if (JsonDocument.Parse(planResult).RootElement.ValueKind == JsonValueKind.Array)
        {
            pullRequests.AddRange(JsonSerializer.Deserialize<PullRequest[]>(planResult)!);

            // tokens
            result = JsonSerializer.Serialize(pullRequests);
            int tokensUsed = CountTokens(result);
            while (tokensUsed > tokenAllowance)
            {
                pullRequests.RemoveAt(pullRequests.Count - 1);
                result = JsonSerializer.Serialize(pullRequests);
                tokensUsed = CountTokens(result);
            }
        }
        else
        {
            pullRequests.Add(JsonSerializer.Deserialize<PullRequest>(planResult)!);
            result = JsonSerializer.Serialize(pullRequests);
        }

        return result;
    }

    /// <summary>
    /// Try to extract json from the planner response as if it were from an OpenAPI plugin.
    /// </summary>
    private static bool TryExtractJsonFromOpenApiPlanResult(string openApiPluginResponse, ILogger logger, out string json)
    {
        try
        {
            JsonNode? jsonNode = JsonNode.Parse(openApiPluginResponse);
            string contentType = jsonNode?["contentType"]?.ToString() ?? string.Empty;
            if (contentType.StartsWith("application/json", StringComparison.InvariantCultureIgnoreCase))
            {
                var content = jsonNode?["content"]?.ToString() ?? string.Empty;
                if (!string.IsNullOrWhiteSpace(content))
                {
                    json = content;
                    return true;
                }
            }
        }
        catch (JsonException)
        {
            logger.LogWarning("Unable to extract JSON from planner response, it is likely not from an OpenAPI plugin.");
        }
        catch (InvalidOperationException)
        {
            logger.LogWarning("Unable to extract JSON from planner response, it may already be proper JSON.");
        }

        json = string.Empty;
        return false;
    }

    /// <summary>
    /// Custom token counter.
    /// </summary>
    private static int CountTokens(string input)
    {
        return input.Length / 4;
    }
}
