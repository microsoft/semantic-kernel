// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// A repeat of <see cref="Step3_Chat"/> with logging enabled via assignment
/// of a <see cref="LoggerFactory"/> to <see cref="AgentChat.LoggerFactory"/>.
/// </summary>
/// <remarks>
/// Samples become super noisy with logging always enabled.
/// </remarks>
public class Step7_Logging(ITestOutputHelper output) : BaseTest(output)
{
    private const string ReviewerName = "ArtDirector";
    private const string ReviewerInstructions =
        """
        You are an art director who has opinions about copywriting born of a love for David Ogilvy.
        The goal is to determine if the given copy is acceptable to print.
        If so, state that it is approved.
        If not, provide insight on how to refine suggested copy without examples.
        """;

    private const string CopyWriterName = "CopyWriter";
    private const string CopyWriterInstructions =
        """
        You are a copywriter with ten years of experience and are known for brevity and a dry humor.
        The goal is to refine and decide on the single best copy as an expert in the field.
        Only provide a single proposal per response.
        You're laser focused on the goal at hand.
        Don't waste time with chit chat.
        Consider suggestions when refining an idea.
        """;

    [Fact]
    public async Task UseLoggerFactoryWithAgentGroupChatAsync()
    {
        // Define the agents
        ChatCompletionAgent agentReviewer =
            new()
            {
                Instructions = ReviewerInstructions,
                Name = ReviewerName,
                Kernel = this.CreateKernelWithChatCompletion(),
                LoggerFactory = this.LoggerFactory,
            };

        ChatCompletionAgent agentWriter =
            new()
            {
                Instructions = CopyWriterInstructions,
                Name = CopyWriterName,
                Kernel = this.CreateKernelWithChatCompletion(),
                LoggerFactory = this.LoggerFactory,
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat =
            new(agentWriter, agentReviewer)
            {
                // This is all that is required to enable logging across the agent framework/
                LoggerFactory = this.LoggerFactory,
                ExecutionSettings =
                    new()
                    {
                        // Here a TerminationStrategy subclass is used that will terminate when
                        // an assistant message contains the term "approve".
                        TerminationStrategy =
                            new ApprovalTerminationStrategy()
                            {
                                // Only the art-director may approve.
                                Agents = [agentReviewer],
                                // Limit total number of turns
                                MaximumIterations = 10,
                            }
                    }
            };

        // Invoke chat and display messages.
        string input = "concept: maps made out of egg cartons.";
        chat.Add(new ChatMessageContent(AuthorRole.User, input));
        Console.WriteLine($"# {AuthorRole.User}: '{input}'");

        await foreach (ChatMessageContent content in chat.InvokeAsync())
        {
            Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        Console.WriteLine($"# IS COMPLETE: {chat.IsComplete}");
    }

    private sealed class ApprovalTerminationStrategy : TerminationStrategy
    {
        // Terminate when the final message contains the term "approve"
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(history[history.Count - 1].Content?.Contains("approve", StringComparison.OrdinalIgnoreCase) ?? false);
    }
}
