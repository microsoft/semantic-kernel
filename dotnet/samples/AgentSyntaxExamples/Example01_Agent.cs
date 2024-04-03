// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using AgentSyntaxExamples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Example01_Agent : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: AgentInventory.ParrotInstructions,
                name: AgentInventory.ParrotName)
            {
                InstructionArguments = new() { { "count", 3 } },
            };

        // Create a nexus for agent interaction. For more, see: Example03_Chat.
        var nexus = new TestChat();

        // Respond to user input
        await WriteAgentResponseAsync("Fortune favors the bold.");
        await WriteAgentResponseAsync("I came, I saw, I conquered.");
        await WriteAgentResponseAsync("Practice makes perfect.");

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponseAsync(string input)
        {
            await foreach (var content in nexus.InvokeAsync(agent, input))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example01_Agent(ITestOutputHelper output)
        : base(output)
    {
        // Nothing to do...
    }

    /// <summary>
    /// A basic nexus for the agent example.
    /// </summary>
    /// <remarks>
    /// For further exploration of AgentNexus, see: Example03_Chat.
    /// </remarks>
    private sealed class TestChat : AgentNexus
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            Agent agent,
            string? input = null,
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(agent, CreateUserMessage(input), cancellationToken);
    }
}
