// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example shows how to create a plugin class and interact with as described at
/// https://learn.microsoft.com/en-us/semantic-kernel/overview/
/// This sample uses function calling, so it only works on models newer than 0613.
/// </summary>
public class Example02_Plugin : BaseTest
{
    [Fact(Skip = "Test requires input from stdin and we want to keep calls to Console.ReadLine() for clarity in example")]
    public async Task RunAsync()
    {
        this.WriteLine("======== Plugin ========");

        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            this.WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        // Create kernel
        // <KernelCreation>
        var builder = Kernel.CreateBuilder()
                            .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);
        builder.Plugins.AddFromType<LightPlugin>();
        Kernel kernel = builder.Build();
        // </KernelCreation>

        // <Chat>

        // Create chat history
        var history = new ChatHistory();

        // Get chat completion service
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Start the conversation
        Console.Write("User > ");
        string? userInput;
        while ((userInput = Console.ReadLine()) != null)
        {
            // Add user input
            history.AddUserMessage(userInput);

            // Enable auto function calling
            OpenAIPromptExecutionSettings openAIPromptExecutionSettings = new()
            {
                ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
            };

            // Get the response from the AI
            var result = await chatCompletionService.GetChatMessageContentAsync(
                history,
                executionSettings: openAIPromptExecutionSettings,
                kernel: kernel);

            // Print the results
            Console.WriteLine("Assistant > " + result);

            // Add the message from the agent to the chat history
            history.AddMessage(result.Role, result.Content ?? string.Empty);

            // Get user input again
            Console.Write("User > ");
        }
        // </Chat>
    }

    public Example02_Plugin(ITestOutputHelper output) : base(output)
    {
    }
}

#pragma warning disable CA1024 // Use properties where appropriate
// <LightPlugin>
public class LightPlugin
{
    public bool IsOn { get; set; } = false;

    [KernelFunction]
    [Description("Gets the state of the light.")]
    public string GetState() => this.IsOn ? "on" : "off";

    [KernelFunction]
    [Description("Changes the state of the light.'")]
    public string ChangeState(bool newState)
    {
        this.IsOn = newState;
        var state = this.GetState();

        // Print the state to the console
        Console.ForegroundColor = ConsoleColor.DarkBlue;
        Console.WriteLine($"[Light is now {state}]");
        Console.ResetColor();

        return state;
    }
}
// </LightPlugin>
#pragma warning restore CA1024 // Use properties where appropriate
