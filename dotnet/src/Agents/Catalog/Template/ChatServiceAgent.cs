// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.Template;

/// <summary>
/// An example <see cref="ServiceAgent"/> based on chat-completion API.
/// As a <see cref="ComposedServiceAgent"/>, the inner agent is entirely
/// responsible to provide the reponse based on its definition and tooling.
/// </summary>
[ServiceAgentProvider<ChatServiceAgentProvider>()]
public sealed class ChatServiceAgent : ComposedServiceAgent
{
    private const string AgentDescription =
        """
        An example agent that talks like a pirate.
        """;

    private const string AgentInstructions =
        """
        Repeat the most recent user input in the voice of a pirate.
        """;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatServiceAgent"/> class.
    /// </summary>
    public ChatServiceAgent()
    {
        this.Description = AgentDescription;
    }

    /// <inheritdoc/>
    protected override Task<Agent> CreateAgentAsync(CancellationToken cancellationToken)
    {
        ChatCompletionAgent agent =
            new()
            {
                Name = this.Name,
                Description = AgentDescription,
                Instructions = AgentInstructions,
                Kernel = this.Kernel,
                Arguments =
                    this.Arguments ??
                    new KernelArguments(
                        new PromptExecutionSettings()
                        {
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
                        }),
            };

        return Task.FromResult<Agent>(agent);
    }
}
