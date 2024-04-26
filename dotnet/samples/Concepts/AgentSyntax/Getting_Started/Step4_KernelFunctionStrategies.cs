// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

/// <summary>
/// Demonstrate usage of <see cref="KernelFunctionTerminationStrategy"/> and <see cref="KernelFunctionSelectionStrategy"/>
/// to manage <see cref="AgentGroupChat"/> execution.
/// </summary>
public class Step4_KernelFunctionStrategies(ITestOutputHelper output) : BaseTest(output)
{
    private const string ReviewerName = "ArtDirector";
    private const string ReviewerInstructions =
        """
        You are an art director who has opinions about copywriting born of a love for David Ogilvy.
        The goal is to determine if the given copy is acceptable to print.
        If so, state that it is approved.
        If not, provide insight on how to refine suggested copy without examples.
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

        KernelFunction terminationFunction =
            KernelFunctionFactory.CreateFromPrompt(
                """
                Determine if the copy has been approved.  If so, respond with a single word: yes

                History:
                {{$history}}
                """);

        KernelFunction selectionFunction =
            KernelFunctionFactory.CreateFromPrompt(
                """
                You are in a role playing game.
                Carefully read the conversation history and carry on the conversation by specifying only the name of player to take the next turn.

                The available names are:
                {{$agents}}

                History:
                {{$history}}
                """);

        // Create a chat for agent interaction.
        AgentGroupChat chat =
            new(agentWriter, agentReviewer)
            {
                ExecutionSettings =
                    new()
                    {
                        // Here KernelFunctionTerminationStrategy will terminate
                        // when the art-director has given their approval.
                        TerminationStrategy =
                            new KernelFunctionTerminationStrategy(terminationFunction, CreateKernelWithChatCompletion())
                            {
                                // Only the art-director may approve.
                                Agents = [agentReviewer],
                                // Customer result parser to determine if the response is "yes"
                                ResultParser = (result) => result.GetValue<string>()?.Contains("yes", StringComparison.OrdinalIgnoreCase) ?? false,
                                // The prompt variable name for the history argument.
                                HistoryVariableName = "history",
                                // Limit total number of turns
                                MaximumIterations = 10,
                            },
                        // Here a KernelFunctionSelectionStrategy selects agents based on a prompt function.
                        SelectionStrategy =
                            new KernelFunctionSelectionStrategy(selectionFunction, CreateKernelWithChatCompletion())
                            {
                                // Returns the entire result value as a string.
                                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
                                // The prompt variable name for the agents argument.
                                AgentsVariableName = "agents",
                                // The prompt variable name for the history argument.
                                HistoryVariableName = "history",
                            },
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
}
