// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how two agents (one of which is a Bedrock agent) can chat with each other.
/// </summary>
public class Step06_BedrockAgent_AgentChat(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        return new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
    }

    /// <summary>
    /// Demonstrates how to put two <see cref="BedrockAgent"/> instances in a chat.
    /// </summary>
    [Fact]
    public async Task UseAgentWithAgentChat()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step06_BedrockAgent_AgentChat");
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Instructions = "You're a translator who helps users understand the content in Spanish.",
            Name = "Translator",
            Kernel = this.CreateKernelWithChatCompletion(),
        };

        // Create a chat for agent interaction
        var chat = new AgentGroupChat(bedrockAgent, chatCompletionAgent)
        {
            ExecutionSettings = new()
            {
                // Terminate after two turns: one from the bedrock agent and one from the chat completion agent.
                // Note: each invoke will terminate after two turns, and we are invoking the group chat for each user query.
                TerminationStrategy = new MultiTurnTerminationStrategy(2),
            }
        };

        // Respond to user input
        string[] userQueries = [
            "Why is the sky blue in one sentence?",
            "Why do we have seasons in one sentence?"
        ];
        try
        {
            foreach (var userQuery in userQueries)
            {
                chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, userQuery));
                await foreach (var response in chat.InvokeAsync())
                {
                    if (response.Content != null)
                    {
                        this.Output.WriteLine($"[{response.AuthorName}]: {response.Content}");
                    }
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    internal sealed class MultiTurnTerminationStrategy : TerminationStrategy
    {
        public MultiTurnTerminationStrategy(int turns)
        {
            this.MaximumIterations = turns;
        }

        /// <inheritdoc/>
        protected override Task<bool> ShouldAgentTerminateAsync(
            Agent agent,
            IReadOnlyList<ChatMessageContent> history,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult(false);
        }
    }
}
