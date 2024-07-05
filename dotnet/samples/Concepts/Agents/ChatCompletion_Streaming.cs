// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class ChatCompletion_Streaming(ITestOutputHelper output) : BaseTest(output)
{
    private const string ParrotName = "Parrot";
    private const string ParrotInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

    [Fact]
    public async Task UseStreamingChatCompletionAgentAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = ParrotName,
                Instructions = ParrotInstructions,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        ChatHistory chat = [];

        // Respond to user input
        await InvokeAgentAsync("Fortune favors the bold.");
        await InvokeAgentAsync("I came, I saw, I conquered.");
        await InvokeAgentAsync("Practice makes perfect.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.Add(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            StringBuilder builder = new();
            await foreach (StreamingChatMessageContent message in agent.InvokeStreamingAsync(chat))
            {
                if (string.IsNullOrEmpty(message.Content))
                {
                    continue;
                }

                if (builder.Length == 0)
                {
                    Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}:");
                }

                Console.WriteLine($"\t > streamed: '{message.Content}'");
                builder.Append(message.Content);
            }

            if (builder.Length > 0)
            {
                // Display full response and capture in chat history
                Console.WriteLine($"\t > complete: '{builder}'");
                chat.Add(new ChatMessageContent(AuthorRole.Assistant, builder.ToString()) { AuthorName = agent.Name });
            }
        }
    }
}
