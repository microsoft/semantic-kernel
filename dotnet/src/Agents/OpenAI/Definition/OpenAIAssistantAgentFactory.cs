// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Agents.Factory;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides a <see cref="IKernelAgentFactory"/> which creates instances of <see cref="ChatCompletionAgent"/>.
/// </summary>
public sealed class OpenAIAssistantAgentFactory : IKernelAgentFactory
{
    /// <summary>
    /// Gets the type of the OpenAI assistant agent.
    /// </summary>
    public static string OpenAIAssistantAgentType => "openai_assistant";

    /// <inheritdoc/>
    public bool TryCreate(Kernel kernel, AgentDefinition agentDefinition, [NotNullWhen(true)] out KernelAgent? result)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition.Type?.Equals(OpenAIAssistantAgentType, System.StringComparison.Ordinal) ?? false)
        {
            result = new OpenAIAssistantAgent()
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
    private static OpenAIClientProvider GetClientProvider(this Kernel kernel)
    {

    }

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
