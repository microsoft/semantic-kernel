// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Interface for any Semantic Kernel agent threads that allow the messages
/// contained in them to be passed to an agent.
/// </summary>
/// <remarks>
/// <para>
/// <see cref="AgentThread"/> types that implement this interface can
/// be used with Agents that do not maintain a server-side chat history
/// and require the entire set of messages, that are needed to generate
/// a response, to be provided to the agent at invocation time.
/// </para>
/// <para>
/// The set of messages returned may be truncated or processed
/// by the <see cref="AgentThread"/> as needed before passed to the
/// agent to achieve a scalable and performant solution.
/// </para>
/// </remarks>
[Experimental("SKEXP0110")]
public interface IAgentThreadRetrievable
{
    /// <summary>
    /// Asynchronously retrieves all messages to be used for the agent invocation.
    /// </summary>
    /// <remarks>
    /// Messages are returned in ascending chronological order.
    /// </remarks>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The messages in the thread.</returns>
    /// <exception cref="InvalidOperationException">The thread has been deleted.</exception>
    IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(CancellationToken cancellationToken = default);
}
