// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

public class ChatMessageAdapter : IChatMessage
{
    private readonly ChatMessage _message;

    public ChatMessageAdapter(ChatMessage message)
    {
        this._message = message;
    }

    public ChatMessageAdapter(ChatRole role, string content) : this(new ChatMessage(role, content))
    {
    }

    public string Role => this._message.Role.ToString();
    public string Content => this._message.Content;
}
