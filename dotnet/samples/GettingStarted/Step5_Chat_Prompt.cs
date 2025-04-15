// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace GettingStarted;

public sealed class Step5_Chat_Prompt(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to construct a chat prompt and invoke it.
    /// </summary>
    [Fact]
    public async Task InvokeChatPrompt()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Invoke the kernel with a chat prompt and display the result
        string chatPrompt = """
            <message role="user">What is Seattle?</message>
            <message role="system">Respond with JSON.</message>
            """;

        Console.WriteLine(await kernel.InvokePromptAsync(chatPrompt));
    }
}
