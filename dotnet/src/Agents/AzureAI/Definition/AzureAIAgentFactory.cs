// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides a <see cref="KernelAgentFactory"/> which creates instances of <see cref="AzureAIAgent"/>.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AzureAIAgentFactory : KernelAgentFactory
{
    /// <summary>
    /// The type of the Azure AI agent.
    /// </summary>
    public const string AzureAIAgentType = "azureai_agent";

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgentFactory"/> class.
    /// </summary>
    public AzureAIAgentFactory()
        : base([AzureAIAgentType])
    {
    }

    /// <inheritdoc/>
    public override async Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        if (agentDefinition.Type?.Equals(AzureAIAgentType, System.StringComparison.Ordinal) ?? false)
        {
            var projectClient = kernel.GetAIProjectClient(agentDefinition);

            AgentsClient client = projectClient.GetAgentsClient();
            Azure.AI.Projects.Agent agent = await client.CreateAgentAsync(
                model: agentDefinition.Model.Id,
                name: agentDefinition.Name,
                description: agentDefinition.Description,
                instructions: agentDefinition.Instructions,
                tools: agentDefinition.GetAzureToolDefinitions(),
                metadata: agentDefinition.GetMetadata(),
                cancellationToken: cancellationToken).ConfigureAwait(false);

            return new AzureAIAgent(agent, client)
            {
                Kernel = kernel,
            };
        }

        return null;
    }
}
