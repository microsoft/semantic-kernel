// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="BedrockAgent"/>.
/// </summary>
public class Step07_BedrockAgent_Declarative(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task OpenAIAssistantAgentWithConfigurationForOpenAIAsync()
    {
        var text =
            $"""
            type: bedrock_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: {TestConfiguration.BedrockAgent.FoundationModel}
              configuration:
                type: bedrock
                agent_resource_role_arn: {TestConfiguration.BedrockAgent.AgentResourceRoleArn}
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text) as BedrockAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    #region private
    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(BedrockAgent agent, string input)
    {
        // Create a thread for the agent conversation.
        string sessionId = BedrockAgent.CreateSessionId();

        try
        {
            await InvokeAgentAsync(input);
        }
        finally
        {
            // TODO how do we cleanup the agent?
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(sessionId, input, null))
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
    }
    #endregion
}
