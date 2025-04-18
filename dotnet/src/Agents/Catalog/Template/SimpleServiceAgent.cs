// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Service;

namespace Microsoft.SemanticKernel.Agents.Template;

/// <summary>
/// As a <see cref="ComposedServiceAgent"/>, the inner agent is entirely
/// responsible to provide the response based on its definition and tooling.
/// </summary>
/// <remarks>
/// This approach doesn't provide for the introduction of custom code
/// to manipulate or intercept the response.  This works well for
/// a case where the focus is the agent's tooling and avoids the need
/// to navigate internal patterns for implementing a customer agent.
/// </remarks>
[ServiceAgentProvider<SimpleServiceAgentProvider>()]
public sealed class SimpleServiceAgent : ComposedServiceAgent
{
    private const string AgentInstructions =
        """
        Repeat the most recent user input in the voice of a pirate.
        """;

    /// <inheritdoc/>
    protected override Task<Agent> CreateAgentAsync(CancellationToken cancellationToken)
    {
        ChatCompletionAgent agent =
            new()
            {
                Name = this.Name,
                Instructions = AgentInstructions,
                Kernel = this.Kernel,
            };

        return Task.FromResult<Agent>(agent);
    }
}
