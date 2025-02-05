// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class CompletionContext
{
    public IList<ChatMessage> ChatMessages { get; init; }

    public object Completion { get; init; }

    public CompletionContext(IList<ChatMessage> chatMessages, object completion)
    {
        this.ChatMessages = chatMessages;
        this.Completion = completion;
    }
}
