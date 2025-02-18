// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Factory;

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
            kernelAgent = await OpenAIAssistantAgent.CreateAsync(
                clientProvider: kernel.GetOpenAIClientProvider(agentDefinition),
                definition: agentDefinition.GetOpenAIAssistantDefinition(),
                kernel: kernel,
                defaultArguments: agentDefinition.GetDefaultKernelArguments(),
                cancellationToken: cancellationToken
                ).ConfigureAwait(false);
        }

        return Task.FromResult<KernelAgent?>(kernelAgent).Result;
    }
}
