// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example demonstrates how to templatize prompts as described at
/// https://learn.microsoft.com/semantic-kernel/prompts/templatizing-prompts
/// </summary>
public class Templates : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        WriteLine("======== Templates ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
                              .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey)
                              .Build();

        // Create a Semantic Kernel template for chat
        var chat = kernel.CreateFunctionFromPrompt(
            @"{{$history}}
            User: {{$request}}
            Assistant: ");

        // Create choices
        List<string> choices = new() { "ContinueConversation", "EndConversation" };

        // Create few-shot examples
        List<ChatHistory> fewShotExamples =
        [
            new ChatHistory()
            {
                new ChatMessageContent(AuthorRole.User, "Can you send a very quick approval to the marketing team?"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "ContinueConversation")
            },
            new ChatHistory()
            {
                new ChatMessageContent(AuthorRole.User, "Thanks, I'm done for now"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "EndConversation")
            }
        ];

        // Create handlebars template for intent
        var getIntent = kernel.CreateFunctionFromPrompt(
            new()
            {
                Template = @"
<message role=""system"">Instructions: What is the intent of this request?
Do not explain the reasoning, just reply back with the intent. If you are unsure, reply with {{choices[0]}}.
Choices: {{choices}}.</message>

{{#each fewShotExamples}}
    {{#each this}}
        <message role=""{{role}}"">{{content}}</message>
    {{/each}}
{{/each}}

{{#each chatHistory}}
    <message role=""{{role}}"">{{content}}</message>
{{/each}}

<message role=""user"">{{request}}</message>
<message role=""system"">Intent:</message>",
                TemplateFormat = "handlebars"
            },
            new HandlebarsPromptTemplateFactory()
        );

        ChatHistory history = new();

        // Start the chat loop
        while (true)
        {
            // Get user input
            Write("User > ");
            var request = ReadLine();

            // Invoke prompt
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
                chat,
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
                    Write(chunk.Role + " > ");
                }

                message += chunk;
                Write(chunk);
            }
            WriteLine();

            // Append to history
            history.AddUserMessage(request!);
            history.AddAssistantMessage(message);
        }
    }

    public Templates(ITestOutputHelper output) : base(output)
    {
        SimulatedInputText = [
            "Can you send an approval to the marketing team?",
            "That is all, thanks."];
    }
}
