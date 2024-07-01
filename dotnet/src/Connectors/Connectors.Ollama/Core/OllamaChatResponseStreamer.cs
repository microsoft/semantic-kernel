// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using OllamaSharp.Models.Chat;
using OllamaSharp.Streamer;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

internal class OllamaChatResponseStreamer : IResponseStreamer<ChatResponseStream>
{
    private readonly ConcurrentQueue<string> _messages = new();
    public void Stream(ChatResponseStream stream)
    {
        if (stream.Message?.Content is null)
        {
            return;
        }

        this._messages.Enqueue(stream.Message.Content);
    }

    public bool TryGetMessage(out string result)
    {
       return this._messages.TryDequeue(out result);
    }
}
