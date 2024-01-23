// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel;
using System.Threading.Tasks;
using Xunit;
using Xunit.Abstractions;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.ChatCompletion;
using System.Collections.Generic;
using System;
using System.Linq;

namespace Examples;

/// <summary>
/// This example demonstrates how to serialize prompts as described at
/// https://learn.microsoft.com/en-us/semantic-kernel/prompts/saving-prompts-as-files
/// </summary>
public class Example31_SerializingPrompts : BaseTest
{
    [Fact(Skip = "Test requires input from stdin and we want to keep calls to Console.ReadLine() for clarity in example")]
    public async Task RunAsync()
    {
        this.WriteLine("======== Serializing Prompts ========");

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

        // Load prompts
        var prompts = kernel.CreatePluginFromPromptDirectory("Prompts");

        // Load prompt from YAML
        using StreamReader reader = new(Assembly.GetExecutingAssembly().GetManifestResourceStream("prompts.getIntent.prompt.yaml")!);
        KernelFunction getIntent = kernel.CreateFunctionFromPromptYaml(
            await reader.ReadToEndAsync(),
            promptTemplateFactory: new HandlebarsPromptTemplateFactory()
        );

        // Create choices
        List<string> choices = new() { "ContinueConversation", "EndConversation" };

        // Create few-shot examples
        List<ChatHistory> fewShotExamples = new()
        {
            new ChatHistory()
            {
                new ChatMessageContent(AuthorRole.User, "Can you send a very quick approval to the marketing team?"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "ContinueConversation")
            },
            new ChatHistory()
            {
                new ChatMessageContent(AuthorRole.User, "Can you send the full update to the marketing team?"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "EndConversation")
            }
        };

        // Create chat history
        ChatHistory history = new();

        // Start the chat loop
        while (true)
        {
            // Get user input
            Console.Write("User > ");
            var request = Console.ReadLine();

            // Invoke handlebars prompt
            var intent = await kernel.InvokeAsync(
                getIntent,
                new()
                {
                    { "request", request },
                    { "choices", choices },
                    { "history", history },
                    { "fewShotExamples", fewShotExamples }
                }
            );

            // End the chat if the intent is "Stop"
            if (intent.ToString() == "EndConversation")
            {
                break;
            }

            // Get chat response
            var chatResult = kernel.InvokeStreamingAsync<StreamingChatMessageContent>(
                prompts["chat"],
                new()
                {
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

    public Example31_SerializingPrompts(ITestOutputHelper output) : base(output)
    {
    }
}
