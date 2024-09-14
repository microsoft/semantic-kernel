// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.SemanticKernel.Agents.Chat;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// An Interface <see cref="IAgentGroupChat"/> for an Agentic Group Chat that supports multi-turn interactions.
/// </summary>
public interface IAgentGroupChat : IAgentChat
{
    /// <summary>
    /// The agents participating in the chat.
    /// </summary>
    IReadOnlyList<Agent> Agents { get; }

    /// <summary>
    /// Settings for defining chat behavior.
    /// </summary>
    AgentGroupChatSettings ExecutionSettings { get; set; }

    /// <summary>
    /// Indicates if completion criteria has been met. If set, no further
    /// agent interactions will occur. Clear to enable more agent interactions.
    /// </summary>
    bool IsComplete { get; set; }

    /// <summary>
    /// Add a <see cref="Agent"/> to the chat.
    /// </summary>
    /// <param name="agent">The <see cref="Agent"/> to add.</param>
    void AddAgent(Agent agent);

    /// <summary>
    /// Process a series of interactions between the <see cref="IAgentGroupChat.Agents"/> that have joined this <see cref="IAgentGroupChat"/>.
    /// The interactions will proceed according to the <see cref="SelectionStrategy"/> and the <see cref="TerminationStrategy"/>
    /// defined via <see cref="IAgentGroupChat.ExecutionSettings"/>.
    /// In the absence of an <see cref="AgentGroupChatSettings.SelectionStrategy"/>, this method will not invoke any agents.
    /// Any agent may be explicitly selected by calling <see cref="IAgentGroupChat.InvokeAsync(Agent, CancellationToken)"/>.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync([EnumeratorCancellation] CancellationToken cancellationToken = default);

    /// <summary>
    /// Process a single interaction between a given <see cref="Agent"/> and an <see cref="IAgentGroupChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync(Agent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default);

    /// <summary>
    /// Process a series of interactions between the <see cref="IAgentGroupChat.Agents"/> that have joined this <see cref="IAgentGroupChat"/>.
    /// The interactions will proceed according to the <see cref="SelectionStrategy"/> and the <see cref="TerminationStrategy"/>
    /// defined via <see cref="IAgentGroupChat.ExecutionSettings"/>.
    /// In the absence of an <see cref="AgentGroupChatSettings.SelectionStrategy"/>, this method will not invoke any agents.
    /// Any agent may be explicitly selected by calling <see cref="IAgentGroupChat.InvokeStreamingAsync(Agent, CancellationToken)"/>.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of streaming messages.</returns>
    IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default);

    /// <summary>
    /// Process a single interaction between a given <see cref="Agent"/> and an <see cref="IAgentGroupChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of streaming messages.</returns>
    IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(Agent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default);
}
