// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate usage of <see cref="KernelFunctionTerminationStrategy"/> and <see cref="KernelFunctionSelectionStrategy"/>
/// to manage <see cref="AgentGroupChat"/> execution.
/// </summary>
public class ComplexChat_NestedShopper(ITestOutputHelper output) : BaseTest(output)
{
    protected override bool ForceOpenAI => true;

    private const string InternalLeaderName = "InternalLeader";
    private const string InternalLeaderInstructions =
        """
        Your job is to clearly and directly communicate the current assistant response to the user.

        If information has been requested, only repeat the request.

        If information is provided, only repeat the information.

        Do not come up with your own shopping suggestions.
        """;

    private const string InternalGiftIdeaAgentName = "InternalGiftIdeas";
    private const string InternalGiftIdeaAgentInstructions =
        """        
        You are a personal shopper that provides gift ideas.

        Only provide ideas when the following is known about the gift recipient:
        - Relationship to giver
        - Reason for gift

        Request any missing information before providing ideas.

        Only describe the gift by name.

        Always immediately incorporate review feedback and provide an updated response.
        """;

    private const string InternalGiftReviewerName = "InternalGiftReviewer";
    private const string InternalGiftReviewerInstructions =
        """
        Review the most recent shopping response.

        Either provide critical feedback to improve the response without introducing new ideas or state that the response is adequate.
        """;

    private const string InnerSelectionInstructions =
        $$$"""
        Select which participant will take the next turn based on the conversation history.
        
        Only choose from these participants:
        - {{{InternalGiftIdeaAgentName}}}
        - {{{InternalGiftReviewerName}}}
        - {{{InternalLeaderName}}}
        
        Choose the next participant according to the action of the most recent participant:
        - After user input, it is {{{InternalGiftIdeaAgentName}}}'a turn.
        - After {{{InternalGiftIdeaAgentName}}} replies with ideas, it is {{{InternalGiftReviewerName}}}'s turn.
        - After {{{InternalGiftIdeaAgentName}}} requests additional information, it is {{{InternalLeaderName}}}'s turn.
        - After {{{InternalGiftReviewerName}}} provides feedback or instruction, it is {{{InternalGiftIdeaAgentName}}}'s turn.
        - After {{{InternalGiftReviewerName}}} states the {{{InternalGiftIdeaAgentName}}}'s response is adequate, it is {{{InternalLeaderName}}}'s turn.
                
        Respond in JSON format.  The JSON schema can include only:
        {
            "name": "string (the name of the assistant selected for the next turn)",
            "reason": "string (the reason for the participant was selected)"
        }
        
        History:
        {{${{{KernelFunctionSelectionStrategy.DefaultHistoryVariableName}}}}}
        """;

    private const string OuterTerminationInstructions =
        $$$"""
        Determine if user request has been fully answered.
        
        Respond in JSON format.  The JSON schema can include only:
        {
            "isAnswered": "bool (true if the user request has been fully answered)",
            "reason": "string (the reason for your determination)"
        }
        
        History:
        {{${{{KernelFunctionTerminationStrategy.DefaultHistoryVariableName}}}}}
        """;

    [Fact]
    public async Task NestedChatWithAggregatorAgentAsync()
    {
        Console.WriteLine($"! {Model}");

        OpenAIPromptExecutionSettings jsonSettings = new() { ResponseFormat = ChatCompletionsResponseFormat.JsonObject };
        OpenAIPromptExecutionSettings autoInvokeSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        ChatCompletionAgent internalLeaderAgent = CreateAgent(InternalLeaderName, InternalLeaderInstructions);
        ChatCompletionAgent internalGiftIdeaAgent = CreateAgent(InternalGiftIdeaAgentName, InternalGiftIdeaAgentInstructions);
        ChatCompletionAgent internalGiftReviewerAgent = CreateAgent(InternalGiftReviewerName, InternalGiftReviewerInstructions);

        KernelFunction innerSelectionFunction = KernelFunctionFactory.CreateFromPrompt(InnerSelectionInstructions, jsonSettings);
        KernelFunction outerTerminationFunction = KernelFunctionFactory.CreateFromPrompt(OuterTerminationInstructions, jsonSettings);

        AggregatorAgent personalShopperAgent =
            new(CreateChat)
            {
                Name = "PersonalShopper",
                Mode = AggregatorMode.Nested,
            };

        AgentGroupChat chat =
            new(personalShopperAgent)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy =
                            new KernelFunctionTerminationStrategy(outerTerminationFunction, CreateKernelWithChatCompletion())
                            {
                                ResultParser =
                                    (result) =>
                                    {
                                        OuterTerminationResult? jsonResult = JsonResultTranslator.Translate<OuterTerminationResult>(result.GetValue<string>());

                                        return jsonResult?.isAnswered ?? false;
                                    },
                                MaximumIterations = 5,
                            },
                    }
            };

        // Invoke chat and display messages.
        Console.WriteLine("\n######################################");
        Console.WriteLine("# DYNAMIC CHAT");
        Console.WriteLine("######################################");

        await InvokeChatAsync("Can you provide three original birthday gift ideas.  I don't want a gift that someone else will also pick.");

        await InvokeChatAsync("The gift is for my adult brother.");

        if (!chat.IsComplete)
        {
            await InvokeChatAsync("He likes photography.");
        }

        Console.WriteLine("\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
        Console.WriteLine(">>>> AGGREGATED CHAT");
        Console.WriteLine(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");

        await foreach (ChatMessageContent content in chat.GetChatMessagesAsync(personalShopperAgent).Reverse())
        {
            Console.WriteLine($">>>> {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        async Task InvokeChatAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (ChatMessageContent content in chat.InvokeAsync(personalShopperAgent))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }

            Console.WriteLine($"\n# IS COMPLETE: {chat.IsComplete}");
        }

        ChatCompletionAgent CreateAgent(string agentName, string agentInstructions) =>
            new()
            {
                Instructions = agentInstructions,
                Name = agentName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        AgentGroupChat CreateChat() =>
                new(internalLeaderAgent, internalGiftReviewerAgent, internalGiftIdeaAgent)
                {
                    ExecutionSettings =
                        new()
                        {
                            SelectionStrategy =
                                new KernelFunctionSelectionStrategy(innerSelectionFunction, CreateKernelWithChatCompletion())
                                {
                                    ResultParser =
                                        (result) =>
                                        {
                                            AgentSelectionResult? jsonResult = JsonResultTranslator.Translate<AgentSelectionResult>(result.GetValue<string>());

                                            string? agentName = string.IsNullOrWhiteSpace(jsonResult?.name) ? null : jsonResult?.name;
                                            agentName ??= InternalGiftIdeaAgentName;

                                            Console.WriteLine($"\t>>>> INNER TURN: {agentName}");

                                            return agentName;
                                        }
                                },
                            TerminationStrategy =
                                new AgentTerminationStrategy()
                                {
                                    Agents = [internalLeaderAgent],
                                    MaximumIterations = 7,
                                    AutomaticReset = true,
                                },
                        }
                };
    }

    private sealed record OuterTerminationResult(bool isAnswered, string reason);

    private sealed record AgentSelectionResult(string name, string reason);

    private sealed class AgentTerminationStrategy : TerminationStrategy
    {
        /// <inheritdoc/>
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(true);
        }
    }
}
