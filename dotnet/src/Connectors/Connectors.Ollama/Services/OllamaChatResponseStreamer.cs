// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Text;
using OllamaSharp.Models.Chat;
using OllamaSharp.Streamer;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

internal class OllamaChatResponseStreamer : IResponseStreamer<ChatResponseStream>
{
    private readonly ConcurrentQueue<string> _messages = new();
    public void Stream(ChatResponseStream stream)
    {
        this._messages.Enqueue(stream.Message.Content);
    }

    public bool TryGetMessage(out string result)
    {
       return this._messages.TryDequeue(out result);
    }
}
