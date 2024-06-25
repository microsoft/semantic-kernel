// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.Extensions.Logging;
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

        /// Create a chat for agent interaction. For more, <see cref="Step3_Chat"/>.
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

            string? authorName = null;
            StringBuilder builder = new();
            await foreach (StreamingChatMessageContent message in agent.InvokeStreamingAsync(chat, this.LoggerFactory.CreateLogger<ChatCompletionAgent>())) // %%%
            {
                if (authorName != message.AuthorName)
                {
                    if (builder.Length > 0)
                    {
                        Console.WriteLine($"\t\t'{builder}'");
                        builder.Clear();
                    }

                    builder.Append(message.Content);

                    authorName = message.AuthorName;
                    Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}:");
                }
            }

            if (builder.Length > 0)
            {
                Console.WriteLine($"\t\t'{builder}'");
            }
        }
    }
}
