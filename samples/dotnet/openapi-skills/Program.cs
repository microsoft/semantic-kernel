// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

Console.WriteLine("Welcome to Semantic Kernel OpenAPI Skills Example!");

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

ILogger<Program> logger = loggerFactory.CreateLogger<Program>();

// Initialize semantic kernel
AIServiceOptions aiOptions = configuration.GetRequiredSection(AIServiceOptions.PropertyName).Get<AIServiceOptions>()
    ?? throw new InvalidOperationException($"Missing configuration for {AIServiceOptions.PropertyName}.");

IKernel kernel = Kernel.Builder
    .WithLogger(logger)
    .Configure(c =>
    {
        switch (aiOptions.Type)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                c.AddAzureChatCompletionService(aiOptions.Models.Completion, aiOptions.Endpoint, aiOptions.Key);
                break;
            case AIServiceOptions.AIServiceType.OpenAI:
                c.AddOpenAIChatCompletionService(aiOptions.Models.Completion, aiOptions.Key);
                break;
            default:
                throw new InvalidOperationException($"Unhandled AI service type {aiOptions.Type}");
        }
    })
    .Build();

// Register GitHub skill
GitHubSkillOptions gitHubOptions = configuration.GetRequiredSection(GitHubSkillOptions.PropertyName).Get<GitHubSkillOptions>()
    ?? throw new InvalidOperationException($"Missing configuration for {GitHubSkillOptions.PropertyName}.");

BearerAuthenticationProvider authenticationProvider = new(() => Task.FromResult(gitHubOptions.Key));

//
// TODO add bigger comment
//
await kernel.ImportOpenApiSkillFromFileAsync(
    skillName: "GitHubSkill",
    filePath: Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "GitHubSkill/openapi.json"),
    authCallback: authenticationProvider.AuthenticateRequestAsync);

//
// TODO bigger comment
//
ActionPlanner planner = new ActionPlanner(kernel, logger: logger);

// Chat
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

    chatHistory.AddUserMessage(input);

    //
    // explain planner -> openapi skill
    //
    Plan plan = await planner.CreatePlanAsync(input);
    if (plan.Steps.Count > 0)
    {
        // TODO inject organization and repo
        SKContext planContext = await plan.InvokeAsync(logger: logger);
        if (planContext.ErrorOccurred)
        {
            logger.LogError("{0}", planContext.LastErrorDescription);
        }
        Console.WriteLine(planContext.Result);
    }

    string reply = await chatGPT.GenerateMessageAsync(chatHistory);
    chatHistory.AddAssistantMessage(reply);

    Console.WriteLine("----------------");
    Console.WriteLine($"Assistant: {reply}");
}
