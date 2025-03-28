// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides a <see cref="KernelAgentFactory"/> which creates instances of <see cref="ChatCompletionAgent"/>.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class ChatCompletionAgentFactory : KernelAgentFactory
{
    /// <summary>
    /// The type of the chat completion agent.
    /// </summary>
    public const string ChatCompletionAgentType = "chat_completion_agent";

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgentFactory"/> class.
    /// </summary>
    public ChatCompletionAgentFactory()
        : base([ChatCompletionAgentType])
    {
    }

    /// <inheritdoc/>
    public override Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, IPromptTemplateFactory? promptTemplateFactory = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        ChatCompletionAgent? kernelAgent = null;
        if (this.IsSupported(agentDefinition))
        {
            kernelAgent = new ChatCompletionAgent()
            {
                Name = agentDefinition.Name,
                Description = agentDefinition.Description,
                Instructions = agentDefinition.Instructions,
                Arguments = agentDefinition.GetDefaultKernelArguments(kernel),
                Kernel = kernel,
                Template = agentDefinition.GetPromptTemplate(kernel, promptTemplateFactory),
                LoggerFactory = kernel.LoggerFactory,
            };
        }

        return Task.FromResult<KernelAgent?>(kernelAgent);
    }
}
