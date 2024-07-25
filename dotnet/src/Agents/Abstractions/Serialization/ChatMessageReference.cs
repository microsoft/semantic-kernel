// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// %%%
/// </summary>
/// <param name="message"></param>
internal sealed class ChatMessageReference(ChatMessageContent message)
{
    public AuthorRole Role => message.Role;

    public IEnumerable<KernelContent> Items => message.Items;

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ModelId => message.ModelId;

    public static IEnumerable<ChatMessageReference> Prepare(IEnumerable<ChatMessageContent> messages) =>
        messages.Select(m => new ChatMessageReference(m));
}
