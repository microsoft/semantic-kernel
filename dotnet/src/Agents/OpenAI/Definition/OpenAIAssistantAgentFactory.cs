// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides a <see cref="AgentFactory"/> which creates instances of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
public sealed class OpenAIAssistantAgentFactory : AgentFactory
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
    public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        if (this.IsSupported(agentDefinition))
        {
            var client = agentDefinition.GetOpenAIClient(kernel);
            AssistantClient assistantClient = client.GetAssistantClient();

            Assistant model;
            if (!string.IsNullOrEmpty(agentDefinition.Id))
            {
                // Get an existing assistant
                model = await assistantClient.GetAssistantAsync(agentDefinition.Id, cancellationToken).ConfigureAwait(false);

                return new OpenAIAssistantAgent(model, assistantClient)
                {
                    Kernel = kernel,
                    Arguments = agentDefinition.GetDefaultKernelArguments(kernel) ?? [],
                    Template = agentDefinition.GetPromptTemplate(kernel, agentCreationOptions?.PromptTemplateFactory),
                    Instructions = agentDefinition.Instructions ?? model.Instructions,
                };
            }

            // Create a new assistant
            Verify.NotNull(agentDefinition.Model);
            Verify.NotNull(agentDefinition.Model.Id);

            var assistantCreationOptions = agentDefinition.CreateAssistantCreationOptions();
            model = await assistantClient.CreateAssistantAsync(agentDefinition.Model.Id, assistantCreationOptions, cancellationToken).ConfigureAwait(false);

            return new OpenAIAssistantAgent(model, assistantClient)
            {
                Kernel = kernel,
                Arguments = agentDefinition.GetDefaultKernelArguments(kernel) ?? [],
                Template = agentDefinition.GetPromptTemplate(kernel, agentCreationOptions?.PromptTemplateFactory),
            };
        }

        return null;
    }
}
