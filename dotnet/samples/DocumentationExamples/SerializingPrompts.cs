// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example demonstrates how to serialize prompts as described at
/// https://learn.microsoft.com/semantic-kernel/prompts/saving-prompts-as-files
/// </summary>
public class SerializingPrompts : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        WriteLine("======== Serializing Prompts ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        var builder = Kernel.CreateBuilder()
                            .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey);
        builder.Plugins.AddFromType<ConversationSummaryPlugin>();
        Kernel kernel = builder.Build();

        // Load prompts
        var prompts = kernel.CreatePluginFromPromptDirectory("./../../../Plugins/Prompts");

        // Load prompt from YAML
        using StreamReader reader = new(Assembly.GetExecutingAssembly().GetManifestResourceStream("Resources." + "getIntent.prompt.yaml")!);
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
        Write("User > ");
        string? userInput;
        while ((userInput = ReadLine()) != null)
        {
            // Invoke handlebars prompt
            var intent = await kernel.InvokeAsync(
                getIntent,
                new()
                {
                    { "request", userInput },
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
                    { "request", userInput },
                    { "history", string.Join("\n", history.Select(x => x.Role + ": " + x.Content)) }
                }
            );

            // Stream the response
            string message = "";
            await foreach (var chunk in chatResult)
            {
                if (chunk.Role.HasValue)
                {
                    Write(chunk.Role + " > ");
                }
                message += chunk;
                Write(chunk);
            }
            WriteLine();

            // Append to history
            history.AddUserMessage(userInput);
            history.AddAssistantMessage(message);

            // Get user input again
            Write("User > ");
        }
    }

    public SerializingPrompts(ITestOutputHelper output) : base(output)
    {
        SimulatedInputText = [
            "Can you send an approval to the marketing team?",
            "That is all, thanks."];
    }
}
