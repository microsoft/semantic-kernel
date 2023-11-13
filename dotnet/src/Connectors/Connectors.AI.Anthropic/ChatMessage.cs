// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// A chat message from Anthropic.
/// </summary>
internal sealed class ChatMessage : ChatMessageBase
{
    public ChatMessage(AuthorRole role, string content, IDictionary<string, string>? additionalProperties = null) : base(role, content, additionalProperties)
    {
    }
}
