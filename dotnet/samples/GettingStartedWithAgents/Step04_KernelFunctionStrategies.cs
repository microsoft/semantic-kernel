// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// Demonstrate usage of <see cref="KernelFunctionTerminationStrategy"/> and <see cref="KernelFunctionSelectionStrategy"/>
/// to manage <see cref="AgentGroupChat"/> execution.
/// </summary>
public class Step04_KernelFunctionStrategies(ITestOutputHelper output) : BaseAgentsTest(output)
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
        Never delimit the response with quotation marks.
        You're laser focused on the goal at hand.
        Don't waste time with chit chat.
        Consider suggestions when refining an idea.
        """;

    [Fact]
    public async Task UseKernelFunctionStrategiesWithAgentGroupChat()
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
            AgentGroupChat.CreatePromptFunctionForStrategy(
                """
                Determine if the copy has been approved.  If so, respond with a single word: yes

                History:
                {{$history}}
                """,
                safeParameterNames: "history");

        KernelFunction selectionFunction =
            AgentGroupChat.CreatePromptFunctionForStrategy(
                $$$"""
                Determine which participant takes the next turn in a conversation based on the the most recent participant.
                State only the name of the participant to take the next turn.
                No participant should take more than one turn in a row.

                Choose only from these participants:
                - {{{ReviewerName}}}
                - {{{CopyWriterName}}}

                Always follow these rules when selecting the next participant:
                - After {{{CopyWriterName}}}, it is {{{ReviewerName}}}'s turn.
                - After {{{ReviewerName}}}, it is {{{CopyWriterName}}}'s turn.

                History:
                {{$history}}
                """,
                safeParameterNames: "history");

        // Limit history used for selection and termination to the most recent message.
        ChatHistoryTruncationReducer strategyReducer = new(1);

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
                                // Save tokens by not including the entire history in the prompt
                                HistoryReducer = strategyReducer,
                            },
                        // Here a KernelFunctionSelectionStrategy selects agents based on a prompt function.
                        SelectionStrategy =
                            new KernelFunctionSelectionStrategy(selectionFunction, CreateKernelWithChatCompletion())
                            {
                                // Always start with the writer agent.
                                InitialAgent = agentWriter,
                                // Returns the entire result value as a string.
                                ResultParser = (result) => result.GetValue<string>() ?? CopyWriterName,
                                // The prompt variable name for the history argument.
                                HistoryVariableName = "history",
                                // Save tokens by not including the entire history in the prompt
                                HistoryReducer = strategyReducer,
                                // Only include the agent names and not the message content
                                EvaluateNameOnly = true,
                            },
                    }
            };

        // Invoke chat and display messages.
        ChatMessageContent message = new(AuthorRole.User, "concept: maps made out of egg cartons.");
        chat.AddChatMessage(message);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in chat.InvokeAsync())
        {
            this.WriteAgentChatMessage(response);
        }

        Console.WriteLine($"\n[IS COMPLETED: {chat.IsComplete}]");
    }
}
