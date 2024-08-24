// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Examples;

/// <summary>
/// This example demonstrates how to templatize prompts as described at
/// https://learn.microsoft.com/semantic-kernel/prompts/templatizing-prompts
/// </summary>
public class Templates(ITestOutputHelper output) : LearnBaseTest([
            "Can you send an approval to the marketing team?",
    "That is all, thanks."], output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Templates ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || apiKey is null)
        {
            Console.WriteLine("Azure OpenAI credentials not found. Skipping example.");

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
        List<string> choices = ["ContinueConversation", "EndConversation"];

        // Create few-shot examples
        List<ChatHistory> fewShotExamples =
        [
            [
                new ChatMessageContent(AuthorRole.User, "Can you send a very quick approval to the marketing team?"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "ContinueConversation")
            ],
            [
                new ChatMessageContent(AuthorRole.User, "Thanks, I'm done for now"),
                new ChatMessageContent(AuthorRole.System, "Intent:"),
                new ChatMessageContent(AuthorRole.Assistant, "EndConversation")
            ]
        ];

        // Create handlebars template for intent
        var getIntent = kernel.CreateFunctionFromPrompt(
            new()
            {
                Template = """
                           <message role="system">Instructions: What is the intent of this request?
                           Do not explain the reasoning, just reply back with the intent. If you are unsure, reply with {{choices.[0]}}.
                           Choices: {{choices}}.</message>

                           {{#each fewShotExamples}}
                               {{#each this}}
                                   <message role="{{role}}">{{content}}</message>
                               {{/each}}
                           {{/each}}

                           {{#each chatHistory}}
                               <message role="{{role}}">{{content}}</message>
                           {{/each}}

                           <message role="user">{{request}}</message>
                           <message role="system">Intent:</message>
                           """,
                TemplateFormat = "handlebars"
            },
            new HandlebarsPromptTemplateFactory()
        );

        ChatHistory history = [];

        // Start the chat loop
        while (true)
        {
            // Get user input
            Console.Write("User > ");
            var request = Console.ReadLine();

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
}
