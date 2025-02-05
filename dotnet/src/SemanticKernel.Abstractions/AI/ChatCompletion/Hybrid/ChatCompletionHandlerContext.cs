// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class ChatCompletionHandlerContext
{
    public IDictionary<IChatClient, CompletionContext?> ChatClients { get; init; }

    public IList<ChatMessage> ChatMessages { get; init; }

    public ChatOptions? Options { get; init; }

    public Kernel? Kernel { get; init; }
}
