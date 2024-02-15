// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents a thread that contains messages.
/// </summary>
public interface IAgentThread
{
    /// <summary>
    /// The thread identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// Add a textual user message to the thread.
    /// </summary>
    /// <param name="message">The user message</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns></returns>
    Task<IChatMessage> AddUserMessageAsync(string message, CancellationToken cancellationToken = default);

    /// <summary>
    /// Advance the thread with the specified agent.
    /// </summary>
    /// <param name="agent">An agent instance.</param>
    /// <param name="arguments">Optional arguments for parameterized instructions</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The resulting agent message(s)</returns>
    IAsyncEnumerable<IChatMessage> InvokeAsync(IAgent agent, KernelArguments? arguments = null, CancellationToken cancellationToken = default);

    /// <summary>
    /// Advance the thread with the specified agent.
    /// </summary>
    /// <param name="agent">An agent instance.</param>
    /// <param name="userMessage">The user message</param>
    /// <param name="arguments">Optional arguments for parameterized instructions</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The resulting agent message(s)</returns>
    IAsyncEnumerable<IChatMessage> InvokeAsync(IAgent agent, string userMessage, KernelArguments? arguments = null, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete current thread.  Terminal state - Unable to perform any
    /// subsequent actions.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteAsync(CancellationToken cancellationToken = default);
}
