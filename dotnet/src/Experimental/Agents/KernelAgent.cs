// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represent a base class for agents.
/// </summary>
public abstract class KernelAgent
{
    /// <summary>
    /// Invokes the agent to process the given messages and generate a response.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    public abstract Task<IReadOnlyList<AgentMessage>> InvokeAsync(IReadOnlyList<AgentMessage> messages, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default);
}
