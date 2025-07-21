// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Interface for any Semantic Kernel agent thread that allow the messages
/// contained in it to be passed to an agent.
/// </summary>
/// <remarks>
/// <para>
/// <see cref="AgentThread"/> types that implement this interface can
/// be used with Agents that do not maintain a server-side chat history, e.g. ChatCompletionAgent.
/// These agents are typically implmented using simple LLMs and therefore
/// require the entire chat history to be provided to the LLM for each invocation.
/// </para>
/// <para>
/// This is in contrast to agents that maintain a server-side chat history, e.g. AzureAIAgentThread,
/// where the chat history is stored on the server and managed by the agent service.
/// </para>
/// <para>
/// The set of messages returned may be truncated or processed
/// by the <see cref="AgentThread"/> as needed before passed to the
/// agent to achieve a scalable and performant solution.
/// </para>
/// <para>
/// This interface can be used to implement custom agent threads, that store messages
/// in a database or 3rd party service, instead of in-memory like done by ChatHistoryAgentThread.
/// </para>
/// </remarks>
[Experimental("SKEXP0110")]
public interface IAgentThreadMessageProvider
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
