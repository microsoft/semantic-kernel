// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Example01_Agent : BaseTest
{
    private const string ParrotName = "Parrot";
    private const string ParrotInstructions = "Repeat the user message in the voice of a pirate and then end with {{$count}} parrot sounds.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                name: ParrotName)
            {
                Instructions = ParrotInstructions,
                InstructionArguments = new() { { "count", 3 } },
            };

        // Create a chat for agent interaction. For more, see: Example03_Chat.
        var chat = new TestChat();

        // Respond to user input
        await WriteAgentResponseAsync("Fortune favors the bold.");
        await WriteAgentResponseAsync("I came, I saw, I conquered.");
        await WriteAgentResponseAsync("Practice makes perfect.");

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponseAsync(string input)
        {
            chat.AddUserMessage(input);
            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example01_Agent(ITestOutputHelper output)
        : base(output)
    { }

    /// <summary>
    /// A simple chat for the agent example.
    /// </summary>
    /// <remarks>
    /// For further exploration of <see cref="AgentChat"/>, see: Example03_Chat.
    /// </remarks>
    private sealed class TestChat : AgentChat
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            Agent agent,
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(agent, cancellationToken);
    }
}
