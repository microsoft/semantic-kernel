// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Examples;

/// <summary>
/// This example shows how to create a plugin class and interact with as described at
/// https://learn.microsoft.com/semantic-kernel/overview/
/// This sample uses function calling, so it only works on models newer than 0613.
/// </summary>
public class Plugin(ITestOutputHelper output) : LearnBaseTest([
            "Hello",
    "Can you turn on the lights"], output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Plugin ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            Console.WriteLine("Azure OpenAI credentials not found. Skipping example.");

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
        while ((userInput = Console.ReadLine()) is not null)
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
}

// <LightPlugin>
public class LightPlugin
{
    public bool IsOn { get; set; } = false;

#pragma warning disable CA1024 // Use properties where appropriate
    [KernelFunction]
    [Description("Gets the state of the light.")]
    public string GetState() => IsOn ? "on" : "off";
#pragma warning restore CA1024 // Use properties where appropriate

    [KernelFunction]
    [Description("Changes the state of the light.'")]
    public string ChangeState(bool newState)
    {
        this.IsOn = newState;
        var state = GetState();

        // Print the state to the console
        Console.WriteLine($"[Light is now {state}]");

        return state;
    }
}
// </LightPlugin>
