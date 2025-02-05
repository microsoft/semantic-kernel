// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class HybridChatClient : IChatClient
{
    private readonly IEnumerable<IChatClient> _chatClients;
    private readonly ChatCompletionHandler _handler;
    private readonly Kernel? _kernel;

    public HybridChatClient(IEnumerable<IChatClient> chatClients, ChatCompletionHandler handler, Kernel? kernel = null)
    {
        this._chatClients = chatClients;
        this._handler = handler;
        this._kernel = kernel;
    }

    public ChatClientMetadata Metadata => new ChatClientMetadata();

    public Task<Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this._handler.CompleteAsync(
            new ChatCompletionHandlerContext
            {
                ChatMessages = chatMessages,
                Options = options,
                ChatClients = this._chatClients.ToDictionary(c => c, c => (CompletionContext?)null),
                Kernel = this._kernel,
            }, cancellationToken);
    }

    public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this._handler.CompleteStreamingAsync(
            new ChatCompletionHandlerContext
            {
                ChatMessages = chatMessages,
                Options = options,
                ChatClients = this._chatClients.ToDictionary(c => c, c => (CompletionContext?)null),
                Kernel = this._kernel
            }, cancellationToken);
    }

    public void Dispose()
    {
        this._handler.Dispose();
    }

    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        return null;
    }
}
