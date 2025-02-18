// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
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
    public bool TryCreate(Kernel kernel, AgentDefinition agentDefinition, [NotNullWhen(true)] out KernelAgent? result)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition.Type?.Equals(ChatCompletionAgentType, System.StringComparison.Ordinal) ?? false)
        {
            result = new ChatCompletionAgent()
            {
                Name = agentDefinition.Name,
                Description = agentDefinition.Description,
                Instructions = agentDefinition.Instructions,
                Arguments = GetKernelArguments(agentDefinition),
                Kernel = kernel,
                LoggerFactory = kernel.LoggerFactory,
            };
            return true;
        }

        result = null;
        return false;
    }

    #region private
    private static KernelArguments GetKernelArguments(AgentDefinition agentDefinition)
    {
        var arguments = new KernelArguments(agentDefinition?.Model?.Options);

        if (agentDefinition is not null)
        {
            // Add default arguments for the agent
            foreach (var input in agentDefinition.Inputs)
            {
                if (!input.IsRequired && input.Default is not null)
                {
                    arguments.Add(input.Name, input.Default);
                }
            }
        }

        return arguments;
    }
    #endregion
}
