// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Gpt;

/// <summary>
/// $$$
/// </summary>
public sealed class GptChannel : AgentChannel
{
    //private readonly string threadId;

    /// <inheritdoc/>
    public override Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? message, CancellationToken cancellationToken)
    {
        throw new NotImplementedException("$$$");
    }

    /// <inheritdoc/>
    public override Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken)
    {
        throw new NotImplementedException("$$$");
    }

    ///// <summary>
    ///// $$$
    ///// </summary>
    ///// <param name="threadId"></param>
    //public GptChannel(string threadId)
    //{
    //    this.threadId = threadId;
    //}
}
