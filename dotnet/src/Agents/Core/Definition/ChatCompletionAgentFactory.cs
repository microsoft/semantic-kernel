// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Factory;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides a <see cref="IKernelAgentFactory"/> which creates instances of <see cref="ChatCompletionAgent"/>.
/// </summary>
public sealed class ChatCompletionAgentFactory : IKernelAgentFactory
{
    /// <summary>
    /// Gets the type of the chat completion agent.
    /// </summary>
    public static string ChatCompletionAgentType => "chat_completion_agent";

    /// <inheritdoc/>
    public async Task<KernelAgent?> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        // TODO Implement template handling

        ChatCompletionAgent? kernelAgent = null;
        if (agentDefinition.Type?.Equals(ChatCompletionAgentType, System.StringComparison.Ordinal) ?? false)
        {
            kernelAgent = new ChatCompletionAgent()
            {
                Name = agentDefinition.Name,
                Description = agentDefinition.Description,
                Instructions = agentDefinition.Instructions,
                Arguments = agentDefinition.GetDefaultKernelArguments(),
                Kernel = kernel,
                LoggerFactory = kernel.LoggerFactory,
            };
        }

        return Task.FromResult<KernelAgent?>(kernelAgent).Result;
    }
}
