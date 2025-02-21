// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides a <see cref="IKernelAgentFactory"/> which creates instances of <see cref="AzureAIAgent"/>.
/// </summary>
public sealed class AzureAIAgentFactory : IKernelAgentFactory
{
    /// <summary>
    /// Gets the type of the Azure AI agent.
    /// </summary>
    public static string AzureAIAgentType => "azureai_agent";

    /// <inheritdoc/>
    public async Task<KernelAgent?> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        KernelAgent? kernelAgent = null;
        if (agentDefinition.Type?.Equals(AzureAIAgentType, System.StringComparison.Ordinal) ?? false)
        {
            var clientProvider = kernel.GetAzureAIClientProvider(agentDefinition);

            AgentsClient client = clientProvider.Client.GetAgentsClient();
            Azure.AI.Projects.Agent agent = await client.CreateAgentAsync(
                model: agentDefinition.Model.Id,
                name: agentDefinition.Name,
                description: agentDefinition.Description,
                instructions: agentDefinition.Instructions,
                tools: agentDefinition.GetAzureToolDefinitions(),
                metadata: agentDefinition.GetMetadata(),
                cancellationToken: cancellationToken).ConfigureAwait(false);

            kernelAgent = new AzureAIAgent(agent, client)
            {
                Kernel = kernel,
            };
        }

        return Task.FromResult<KernelAgent?>(kernelAgent).Result;
    }
}
