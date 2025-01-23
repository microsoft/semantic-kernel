// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step00_Recipies(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseSingleChatCompletionAgentAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Translate the input JSON into markdown.",
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        foreach (string file in Directory.EnumerateFiles(@"C:\Users\crickman\Downloads\recipies"))
        {
            Console.WriteLine("#" + file);
            await InvokeAgentAsync(file);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string filePath)
        {
            ChatHistory chat = [];

            string input = File.ReadAllText(filePath);
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.Add(message);

            ChatMessageContent response = await agent.InvokeAsync(chat).SingleAsync();
            string output = Path.ChangeExtension(filePath, ".md");
            Console.WriteLine(output);
            File.WriteAllText(output, response.Content);
        }
    }
}
