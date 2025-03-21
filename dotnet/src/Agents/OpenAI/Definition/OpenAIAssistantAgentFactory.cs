// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides a <see cref="KernelAgentFactory"/> which creates instances of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
public sealed class OpenAIAssistantAgentFactory : KernelAgentFactory
{
    /// <summary>
    /// The type of the OpenAI assistant agent.
    /// </summary>
    public const string OpenAIAssistantAgentType = "openai_assistant";

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentFactory"/> class.
    /// </summary>
    public OpenAIAssistantAgentFactory()
        : base([OpenAIAssistantAgentType])
    {
    }

    /// <inheritdoc/>
    public override async Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        KernelAgent? kernelAgent = null;
        if (this.IsSupported(agentDefinition))
        {
            var client = agentDefinition.GetOpenAIClient(kernel);
            AssistantClient assistantClient = client.GetAssistantClient();

            var assistantCreationOptions = agentDefinition.CreateAssistantCreationOptions();
            Assistant model = await assistantClient.CreateAssistantAsync(agentDefinition.Model.Id, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

            kernelAgent = new OpenAIAssistantAgent(model, assistantClient)
            {
                Kernel = kernel,
                Arguments = agentDefinition.GetDefaultKernelArguments(kernel) ?? [],
            };
        }

        return kernelAgent;
    }
}
