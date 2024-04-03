// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using AgentSyntaxExamples;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="AgentChat"/> with <see cref="ChatExecutionSettings"/>
/// that inform how chat proceeds with regards to: Agent selection, chat continuation, and maximum
/// number of agent interactions.
/// </summary>
public class Example03_Chat : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        // Define the agents
        ChatCompletionAgent agentReviewer =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: AgentInventory.ReviewerInstructions,
                name: AgentInventory.ReviewerName);

        ChatCompletionAgent agentWriter =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: AgentInventory.CopyWriterInstructions,
                name: AgentInventory.CopyWriterName);

        // Create a nexus for agent interaction.
        var nexus =
            new AgentChat(agentWriter, agentReviewer)
            {
                ExecutionSettings =
                    new()
                    {
                        // In its simplest form, a strategy is simply a delegate or "func"",
                        // but can also be assigned a ContinuationStrategy subclass.
                        // Here, custom logic is expressed as a func that will terminate when
                        // an assistant message contains the term "approve".
                        TerminationStrategy = // ContinuationCriteriaCallback
                                (agent, messages, cancellationToken) =>
                                Task.FromResult(
                                    agent.Id == agentReviewer.Id &&
                                    (messages[messages.Count - 1].Content?.Contains("approve", StringComparison.OrdinalIgnoreCase) ?? false)),
                        // Here a SelectionStrategy subclass is used that selects agents via round-robin ordering,
                        // but a custom func could be utilized if desired. (SelectionCriteriaCallback).
                        SelectionStrategy = new SequentialSelectionStrategy(),
                        // It can be prudent to limit how many turns agents are able to take.
                        // If the chat exits when it intends to continue, the IsComplete property will be false on AgentChat
                        // and the conversation may be resumed, if desired.
                        MaximumIterations = 8,
                    }
            };

        // Invoke chat and display messages.
        await foreach (var content in nexus.InvokeAsync("concept: maps made out of egg cartons."))
        {
            this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }
    }

    public Example03_Chat(ITestOutputHelper output)
        : base(output)
    {
        // Nothing to do...
    }
}
