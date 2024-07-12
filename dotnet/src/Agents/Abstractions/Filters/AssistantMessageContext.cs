// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public class AssistantMessageContext
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    /// <param name="message"></param>
    public AssistantMessageContext(Agent agent, IReadOnlyList<ChatMessageContent> history, ChatMessageContent message)
    {
        this.Agent = agent;
        this.History = history;
        this.Message = message;
    }

    /// <summary>
    /// %%%
    /// </summary>
    public Agent Agent { get; } // %%% METADATA ONLY

    /// <summary>
    /// %%%
    /// </summary>
    public IReadOnlyList<ChatMessageContent> History { get; }

    /// <summary>
    /// %%%
    /// </summary>
    public ChatMessageContent Message { get; }

    /// <summary>
    /// %%%
    /// </summary>
    public CancellationToken CancellationToken { get; internal set; }
}
