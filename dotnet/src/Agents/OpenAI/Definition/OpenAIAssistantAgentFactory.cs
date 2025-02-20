// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Factory;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides a <see cref="IKernelAgentFactory"/> which creates instances of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public sealed class OpenAIAssistantAgentFactory : IKernelAgentFactory
{
    /// <summary>
    /// Gets the type of the OpenAI assistant agent.
    /// </summary>
    public static string OpenAIAssistantAgentType => "openai_assistant";

    /// <inheritdoc/>
    public async Task<KernelAgent?> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        KernelAgent? kernelAgent = null;
        if (agentDefinition.Type?.Equals(OpenAIAssistantAgentType, System.StringComparison.Ordinal) ?? false)
        {
            var clientProvider = kernel.GetOpenAIClientProvider(agentDefinition);
            AssistantClient client = clientProvider.Client.GetAssistantClient();

            var definition = agentDefinition.GetOpenAIAssistantDefinition();
            AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantOptions();
            Assistant model = await client.CreateAssistantAsync(definition.ModelId, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

            kernelAgent = new OpenAIAssistantAgent(model, clientProvider.AssistantClient)
            {
                Kernel = kernel,
                Arguments = agentDefinition.GetDefaultKernelArguments() ?? [],
            };
        }

        return Task.FromResult<KernelAgent?>(kernelAgent).Result;
    }
}
