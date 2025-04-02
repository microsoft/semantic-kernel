// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides a <see cref="AgentFactory"/> which creates instances of <see cref="BedrockAgent"/>.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class BedrockAgentFactory : AgentFactory
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
    public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Name);
        Verify.NotNull(agentDefinition.Description);
        Verify.NotNull(agentDefinition.Instructions);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        if (agentDefinition.Type?.Equals(BedrockAgentType, System.StringComparison.Ordinal) ?? false)
        {
            // create the agent
            var agentResourceRoleArn = GetAgentResourceRoleArn(agentDefinition);
            var agentClient = new AmazonBedrockAgentClient();
            var runtimeClient = new AmazonBedrockAgentRuntimeClient();
            var agentModel = await agentClient.CreateAgentAndWaitAsync(
                new()
                {
                    FoundationModel = agentDefinition.Model!.Id,
                    AgentName = agentDefinition.Name,
                    Description = agentDefinition.Description,
                    Instruction = agentDefinition.Instructions,
                    AgentResourceRoleArn = agentResourceRoleArn,
                },
                cancellationToken
            ).ConfigureAwait(false);

            var agent = new BedrockAgent(agentModel, agentClient, runtimeClient)
            {
                Kernel = kernel,
                Arguments = agentDefinition.GetDefaultKernelArguments(kernel) ?? [],
                Template = agentDefinition.GetPromptTemplate(kernel, agentCreationOptions?.PromptTemplateFactory),
            };

            // create tools from the definition
            await agentDefinition.CreateToolsAsync(agent, cancellationToken).ConfigureAwait(false);

            // wait for the agent to be prepared
            await agentClient.PrepareAgentAndWaitAsync(agentModel, cancellationToken).ConfigureAwait(false);

            return agent;
        }

        return null;
    }

    #region private
    private static string? GetAgentResourceRoleArn(AgentDefinition agentDefinition)
    {
        return agentDefinition.Model?.Connection?.ExtensionData.TryGetValue(AgentResourceRoleArn, out var value) ?? false ? value as string : null;
    }

    #endregion
}
