// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> that is associated with a knowledge base.
/// A Bedrock Knowledge Base is a collection of documents that the agent uses to answer user queries.
/// To learn more about Bedrock Knowledge Base, see:
/// https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
/// </summary>
public class Step05_BedrockAgent_FileSearch(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    // Replace the KnowledgeBaseId with a valid KnowledgeBaseId
    // To learn how to create a Knowledge Base, see:
    // https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html
    private const string KnowledgeBaseId = "[KnowledgeBaseId]";

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
        // Associate the agent with a knowledge base and prepare the agent
        await bedrockAgent.AssociateAgentKnowledgeBaseAsync(
            KnowledgeBaseId,
            "You will find information here.");

        return bedrockAgent;
    }

    /// <summary>
    /// Demonstrates how to use a <see cref="BedrockAgent"/> with file search.
    /// </summary>
    [Fact(Skip = "This test is skipped because it requires a valid KnowledgeBaseId.")]
    public async Task UseAgentWithFileSearchAsync()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step05_BedrockAgent_FileSearch");

        // Respond to user input
        // Assuming the knowledge base contains information about Semantic Kernel.
        // Feel free to modify the user query according to the information in your knowledge base.
        var userQuery = "What is Semantic Kernel?";
        try
        {
            // Customize the request for advanced scenarios
            InvokeAgentRequest invokeAgentRequest = new()
            {
                AgentAliasId = BedrockAgent.WorkingDraftAgentAlias,
                AgentId = bedrockAgent.Id,
                SessionId = BedrockAgent.CreateSessionId(),
                InputText = userQuery,
            };

            var responses = bedrockAgent.InvokeAsync(invokeAgentRequest, null, CancellationToken.None);
            await foreach (var response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }
}
