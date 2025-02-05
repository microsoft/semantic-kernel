// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

public abstract class ChatCompletionHandler : IDisposable
{
    public abstract Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public abstract IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public virtual void Dispose()
    {
    }
}
