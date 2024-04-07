// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
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
    private const string ReviewerName = "ArtDirector";
    private const string ReviewerInstructions = "You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to determine is the given copy is acceptable to print.  If so, state that it is approved.  If not, provide insight on how to refine suggested copy without example.";

    private const string CopyWriterName = "Writer";
    private const string CopyWriterInstructions = "You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agents
        ChatCompletionAgent agentReviewer =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: ReviewerInstructions,
                name: ReviewerName);

        ChatCompletionAgent agentWriter =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: CopyWriterInstructions,
                name: CopyWriterName);

        // Create a nexus for agent interaction.
        var chat =
            new AgentGroupChat(agentWriter, agentReviewer)
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
        string input = "concept: maps made out of egg cartons.";
        chat.AddUserMessage(input);
        this.WriteLine($"# {AuthorRole.User}: '{input}'");

        await foreach (var content in chat.InvokeAsync())
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
