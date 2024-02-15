// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// This example shows how to use chat completion standardized prompts.
public class Example63_ChatCompletionPrompts : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        const string ChatPrompt = @"
            <message role=""user"">What is Seattle?</message>
            <message role=""system"">Respond with JSON.</message>
        ";

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(ChatPrompt);
        var chatPromptResult = await kernel.InvokeAsync(chatSemanticFunction);

        WriteLine("Chat Prompt:");
        WriteLine(ChatPrompt);
        WriteLine("Chat Prompt Result:");
        WriteLine(chatPromptResult);

        WriteLine("Chat Prompt Streaming Result:");
        string completeMessage = string.Empty;
        await foreach (var message in kernel.InvokeStreamingAsync<string>(chatSemanticFunction))
        {
            completeMessage += message;
            Write(message);
        }

        WriteLine("---------- Streamed Content ----------");
        WriteLine(completeMessage);

        /*
        Chat Prompt:
        <message role="user">What is Seattle?</message>
        <message role="system">Respond with JSON.</message>

        Chat Prompt Result:
        {
          "Seattle": {
            "Description": "Seattle is a city located in the state of Washington, in the United States...",
            "Population": "Approximately 753,675 as of 2019",
            "Area": "142.5 square miles",
            ...
          }
        }
        */
    }

    public Example63_ChatCompletionPrompts(ITestOutputHelper output) : base(output)
    {
    }
}
