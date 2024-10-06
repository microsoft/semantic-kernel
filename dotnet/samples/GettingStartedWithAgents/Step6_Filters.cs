// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.Filters;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// Demonstrate usage of <see cref="AgentChat"/> with <see cref="IAgentChatFilter"/>.
/// </summary>
public class Step6_Filters(ITestOutputHelper output) : BaseTest(output)
{
    private const string ReviewerName = "ArtDirector";
    private const string ReviewerInstructions =
        """
        You are an art director who has opinions about copywriting born of a love for David Ogilvy.
        The goal is to determine is the given copy is acceptable to print.
        If so, state that it is approved.
        If not, provide insight on how to refine suggested copy without example.
        """;

    private const string CopyWriterName = "Writer";
    private const string CopyWriterInstructions =
        """
        You are a copywriter with ten years of experience and are known for brevity and a dry humor.
        You're laser focused on the goal at hand. Don't waste time with chit chat.
        The goal is to refine and decide on the single best copy as an expert in the field.
        Consider suggestions when refining an idea.
        """;

    [Fact]
    public async Task RunAsync()
    {
        // Define the agents
        ChatCompletionAgent agentReviewer =
            new()
            {
                Instructions = ReviewerInstructions,
                Name = ReviewerName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        ChatCompletionAgent agentWriter =
            new()
            {
                Instructions = CopyWriterInstructions,
                Name = CopyWriterName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat =
            new(agentWriter, agentReviewer)
            {
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
                            }
                    },
                Filters =
                {
                    new ExampleChatFilter(base.Output)
                }
            };

        // Invoke chat and display messages.
        string input = "concept: maps made out of egg cartons.";
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));
        this.WriteLine($"# {AuthorRole.User}: '{input}'");

        await foreach (var content in chat.InvokeAsync())
        {
            this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        this.WriteLine($"# IS COMPLETE: {chat.IsComplete}");
    }

    private sealed class ApprovalTerminationStrategy : TerminationStrategy
    {
        // Terminate when the final message contains the term "approve"
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(history[history.Count - 1].Content?.Contains("approve", StringComparison.OrdinalIgnoreCase) ?? false);
    }

    private sealed class ExampleChatFilter(ITestOutputHelper output) : IAgentChatFilter
    {
        public void OnAgentInvoked(AgentChatFilterInvokedContext context)
        {
            output.WriteLine($"$ FILTER - {context.Agent.Name}: {nameof(OnAgentInvoked)} #{context.Message.Content?.Length ?? 0}");
        }

        public void OnAgentInvoking(AgentChatFilterInvokingContext context)
        {
            output.WriteLine($"$ FILTER - {context.Agent.Name}: {nameof(OnAgentInvoking)}");
        }
    }
}
