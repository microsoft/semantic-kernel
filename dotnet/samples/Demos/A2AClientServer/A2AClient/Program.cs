// Copyright (c) Microsoft. All rights reserved.

using System.CommandLine;
using System.CommandLine.Invocation;
using System.Reflection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace A2A;

public static class Program
{
    public static async Task<int> Main(string[] args)
    {
        // Create root command with options
        var rootCommand = new RootCommand("A2AClient")
        {
            s_agentOption,
        };

        // Replace the problematic line with the following:
        rootCommand.SetHandler(RunCliAsync);

        // Run the command
        return await rootCommand.InvokeAsync(args);
    }

    public static async System.Threading.Tasks.Task RunCliAsync(InvocationContext context)
    {
        string agent = context.ParseResult.GetValueForOption<string>(s_agentOption)!;

        await RunCliAsync(agent);
    }

    #region private
    private static readonly Option<string> s_agentOption = new(
                "--agent",
                getDefaultValue: () => "http://localhost:10000",
                description: "Agent URL");

    private static async System.Threading.Tasks.Task RunCliAsync(string agentUrl)
    {
        // Set up the logging
        using var loggerFactory = LoggerFactory.Create(builder =>
        {
            builder.AddConsole();
            builder.SetMinimumLevel(LogLevel.Information);
        });
        var logger = loggerFactory.CreateLogger("A2AClient");

        // Retrieve configuration settings
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();
        string apiKey = configRoot["OPENAI_API_KEY"] ?? throw new ArgumentException("OPENAI_API_KEY must be provided");
        string modelId = configRoot["OPENAI_CHAT_MODEL_ID"] ?? "gpt-4.1";
        string baseAddress = configRoot["AGENT_URL"] ?? "http://localhost:5000";

        // Create the Host agent
        var hostAgent = new HostClientAgent(logger);
        await hostAgent.InitializeAgentAsync(modelId, apiKey, baseAddress);

        try
        {
            while (true)
            {
                // Get user message
                Console.Write("\nUser (:q or quit to exit): ");
                string? message = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(message))
                {
                    Console.WriteLine("Request cannot be empty.");
                    continue;
                }

                if (message == ":q" || message == "quit")
                {
                    break;
                }

                Console.ForegroundColor = ConsoleColor.Cyan;
                await foreach (AgentResponseItem<ChatMessageContent> response in hostAgent.Agent!.InvokeAsync(message))
                {
                    Console.WriteLine($"Agent: {response.Message.Content}");
                }
                Console.ResetColor();
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred while running the A2AClient");
            return;
        }
    }
    #endregion
}
