// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides a <see cref="KernelAgentFactory"/> which creates instances of <see cref="BedrockAgent"/>.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class BedrockAgentFactory : KernelAgentFactory
{
    /// <summary>
    /// The type of the Bedrock agent.
    /// </summary>
    public const string BedrockAgentType = "bedrock_agent";

    private const string AgentResourceRoleArn = "agent_resource_role_arn";

    /// <summary>
    /// Initializes a new instance of the <see cref="BedrockAgentFactory"/> class.
    /// </summary>
    public BedrockAgentFactory()
        : base([BedrockAgentType])
    {
    }

    /// <inheritdoc/>
    public override async Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Name);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        if (agentDefinition.Type?.Equals(BedrockAgentType, System.StringComparison.Ordinal) ?? false)
        {
            var agentResourceRoleArn = GetAgentResourceRoleArn(agentDefinition);
            using var agentClient = new AmazonBedrockAgentClient();
            var agentModel = await agentClient.CreateAndPrepareAgentAsync(
                    new()
                    {
                        FoundationModel = agentDefinition.Model!.Id,
                        AgentName = agentDefinition.Name,
                        Description = agentDefinition.Description ?? string.Empty,
                        Instruction = agentDefinition.Instructions ?? string.Empty,
                        AgentResourceRoleArn = agentResourceRoleArn,
                    },
                    cancellationToken
                ).ConfigureAwait(false);
            return new BedrockAgent(agentModel, agentClient)
            {
                Kernel = kernel
            };
        }

        return null;
    }

    #region private
    private static string? GetAgentResourceRoleArn(AgentDefinition agentDefinition)
    {
        return agentDefinition.Model?.Configuration?.ExtensionData.TryGetValue(AgentResourceRoleArn, out var value) ?? false ? value as string : null;
    }
    #endregion
}
