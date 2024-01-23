// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example demonstrates how to configure prompts as described at
/// https://learn.microsoft.com/en-us/semantic-kernel/prompts/configure-prompts
/// </summary>
public class Example29_ConfiguringPrompts : BaseTest
{
    [Fact(Skip = "Test requires input from stdin and we want to keep calls to Console.ReadLine() for clarity in example")]
    public async Task RunAsync()
    {
        this.WriteLine("======== Configuring Prompts ========");

        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            this.WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        var builder = Kernel.CreateBuilder()
                            .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);
        builder.Plugins.AddFromType<ConversationSummaryPlugin>();
        Kernel kernel = builder.Build();

        // <FunctionFromPrompt>
        // Create a template for chat with settings
        var chat = kernel.CreateFunctionFromPrompt(
            new PromptTemplateConfig()
            {
                Name = "Chat",
                Description = "Chat with the assistant.",
                Template = @"{{ConversationSummaryPlugin.SummarizeConversation $history}}
                            User: {{$request}}
                            Assistant: ",
                TemplateFormat = "semantic-kernel",
                InputVariables = new List<InputVariable>()
                {
                    new() { Name = "history", Description = "The history of the conversation.", IsRequired = false, Default = "" },
                    new() { Name = "request", Description = "The user's request.", IsRequired = true }
                },
                ExecutionSettings =
                {
                    {
                        "default",
                        new OpenAIPromptExecutionSettings()
                        {
                            MaxTokens = 1000,
                            Temperature = 0
                        }
                    },
                    {
                        "gpt-3.5-turbo", new OpenAIPromptExecutionSettings()
                        {
                            ModelId = "gpt-3.5-turbo-0613",
                            MaxTokens = 4000,
                            Temperature = 0.2
                        }
                    },
                    {
                        "gpt-4",
                        new OpenAIPromptExecutionSettings()
                        {
                            ModelId = "gpt-4-1106-preview",
                            MaxTokens = 8000,
                            Temperature = 0.3
                        }
                    }
                }
            }
        );
        // </FunctionFromPrompt>

        // Create chat history and choices
        ChatHistory history = new();

        // Start the chat loop
        while (true)
        {
            // Get user input
            Console.Write("User > ");
            var request = Console.ReadLine();

            // Get chat response
            var chatResult = kernel.InvokeStreamingAsync<StreamingChatMessageContent>(
                chat,
                new() {
            { "request", request },
            { "history", string.Join("\n", history.Select(x => x.Role + ": " + x.Content)) }
                }
            );

            // Stream the response
            string message = "";
            await foreach (var chunk in chatResult)
            {
                if (chunk.Role.HasValue)
                {
                    Console.Write(chunk.Role + " > ");
                }
                message += chunk;
                Console.Write(chunk);
            }
            Console.WriteLine();

            // Append to history
            history.AddUserMessage(request!);
            history.AddAssistantMessage(message);
        }
    }

    public Example29_ConfiguringPrompts(ITestOutputHelper output) : base(output)
    {
    }
}
