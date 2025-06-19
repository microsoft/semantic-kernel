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
        var rootCommand = new RootCommand("A2AClient");
        rootCommand.SetHandler(HandleCommandsAsync);

        // Run the command
        return await rootCommand.InvokeAsync(args);
    }

    public static async System.Threading.Tasks.Task HandleCommandsAsync(InvocationContext context)
    {
        await RunCliAsync();
    }

    #region private
    private static async System.Threading.Tasks.Task RunCliAsync()
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
        var apiKey = configRoot["A2AClient:ApiKey"] ?? throw new ArgumentException("A2AClient:ApiKey must be provided");
        var modelId = configRoot["A2AClient:ModelId"] ?? "gpt-4.1";
        var agentUrls = configRoot["A2AClient:AgentUrls"] ?? "http://localhost:5000/ http://localhost:5001/ http://localhost:5002/";

        // Create the Host agent
        var hostAgent = new HostClientAgent(logger);
        await hostAgent.InitializeAgentAsync(modelId, apiKey, agentUrls!.Split(" "));
        AgentThread thread = new ChatHistoryAgentThread();
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

                await foreach (AgentResponseItem<ChatMessageContent> response in hostAgent.Agent!.InvokeAsync(message, thread))
                {
                    Console.ForegroundColor = ConsoleColor.Cyan;
                    Console.WriteLine($"Agent: {response.Message.Content}");
                    Console.ResetColor();

                    thread = response.Thread;
                }
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
