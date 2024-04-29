// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Examples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;
using Xunit;
using Xunit.Abstractions;

/// <summary>
/// Demonstrate usage of <see cref="KernelFunctionTerminationStrategy"/> and <see cref="KernelFunctionSelectionStrategy"/>
/// to manage <see cref="AgentGroupChat"/> execution.
/// </summary>
public class ComplexChat_NestedShopper(ITestOutputHelper output) : BaseTest(output)
{
    protected override bool ForceOpenAI => true;

    private const string LeaderName = "Spokesperson";
    private const string LeaderInstructions =
        """
        Your job is to clearly and directly communicate the current assistant response to the user.

        If information has been requested, only repeat the request.

        If information is provided, only repeat the information.

        Do not come up with your own shopping suggestions.
        """;

    private const string ShopperName = "PersonalShopper";
    private const string ShopperInstructions =
        """        
        You are a personal shopper that provides gift ideas.

        Only provide ideas when the following is known about the gift recipient:
        - Relationship to giver
        - Reason for gift

        Request any missing information before providing ideas.

        Only describe the gift by name.

        Always immediately incorporate review feedback and provide an updated response.
        """;

    private const string ReviewerName = "ShopperReviewer";
    private const string ReviewerInstructions =
        """
        Review the most recent shopping response.

        Either provide critical feedback to improve the response without introducing new ideas or state that the response is adequate.
        """;

    private const string InnerSelectionInstructions =
        $$$"""
        Select which participant will take the next turn based on the conversation history.
        
        Only choose from these participants:
        - {{{ShopperName}}}
        - {{{ReviewerName}}}
        - {{{LeaderName}}}
        
        Choose the next participant according to the action of the most recent participant:
        - After user input, it is {{{ShopperName}}}'a turn.
        - After {{{ShopperName}}} replies with ideas, it is {{{ReviewerName}}}'s turn.
        - After {{{ShopperName}}} requests additional information, it is {{{LeaderName}}}'s turn.
        - After {{{ReviewerName}}} provides feedback or instruction, it is {{{ShopperName}}}'s turn.
        - After {{{ReviewerName}}} states the {{{ShopperName}}}'s response is adequate, it is {{{LeaderName}}}'s turn.
                
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
    public async Task RunAsync()
    {
        this.WriteLine($"! {Model}");

        OpenAIPromptExecutionSettings jsonSettings = new() { ResponseFormat = ChatCompletionsResponseFormat.JsonObject };
        OpenAIPromptExecutionSettings autoInvokeSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        ChatCompletionAgent agentManager = CreateAgent(LeaderName, LeaderInstructions);
        ChatCompletionAgent agentShopper = CreateAgent(ShopperName, ShopperInstructions);
        ChatCompletionAgent agentReviewer = CreateAgent(ReviewerName, ReviewerInstructions);

        KernelFunction innerSelectionFunction = KernelFunctionFactory.CreateFromPrompt(InnerSelectionInstructions, jsonSettings);
        KernelFunction outerTerminationFunction = KernelFunctionFactory.CreateFromPrompt(OuterTerminationInstructions, jsonSettings);

        AggregatorAgent agentShopperGroup = new(CreateChat) { Name = "Shopper" };

        AgentGroupChat chat =
            new(agentShopperGroup)
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
        this.WriteLine("\n######################################");
        this.WriteLine("# DYNAMIC CHAT");
        this.WriteLine("######################################");

        await InvokeChatAsync("Can you provide three original birthday gift ideas.  I don't want a gift that someone else will also pick.");

        await InvokeChatAsync("The gift is for my adult brother.");

        if (!chat.IsComplete)
        {
            await InvokeChatAsync("He likes photography.");
        }

        await using StreamWriter writer = File.CreateText($"C:/agents/{this.GetType().Name}-Inner.txt");

        writer.WriteLine("\n\n######################################");
        writer.WriteLine($"# {chat.GetType().Name}");
        writer.WriteLine("######################################");

        await foreach (var content in chat.GetChatMessagesAsync(agentShopperGroup).Reverse())
        {
            writer.WriteLine("\n#######");
            writer.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        async Task InvokeChatAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            this.WriteLine("\n#######");
            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agentShopperGroup))
            {
                this.WriteLine("\n#######");
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }

            this.WriteLine($"\n# IS COMPLETE: {chat.IsComplete}");
        }

        ChatCompletionAgent CreateAgent(string agentName, string agentInstructions) =>
            new()
            {
                Instructions = agentInstructions,
                Name = agentName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        AgentGroupChat CreateChat() =>
                new(agentManager, agentReviewer, agentShopper)
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
                                            agentName ??= ShopperName;

                                            this.WriteLine($"\n? NEXT: {agentName} - {jsonResult?.reason ?? "0"}");

                                            return agentName;
                                        }
                                },
                            TerminationStrategy =
                                new AgentTerminationStrategy()
                                {
                                    Agents = [agentManager],
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
