// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// Represents a <see cref="ChatMessageContent"/> for serialization without metadata.
/// </summary>
/// <param name="message">The referenced message</param>
[Experimental("SKEXP0110")]
public sealed class ChatMessageReference(ChatMessageContent message)
{
    /// <summary>
    /// Gets the referenced <see cref="ChatMessageContent.AuthorName"/> property.
    /// </summary>
    public string? AuthorName => message.AuthorName;

    /// <summary>
    /// Gets the referenced <see cref="ChatMessageContent.Role"/> property.
    /// </summary>
    public AuthorRole Role => message.Role;

    /// <summary>
    /// Gets the referenced <see cref="ChatMessageContent.Items"/> collection.
    /// </summary>
    public IEnumerable<KernelContent> Items => message.Items;

    /// <summary>
    /// Gets the referenced <see cref="KernelContent.ModelId"/> property.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ModelId => message.ModelId;

    /// <summary>
    /// Gets the referenced <see cref="KernelContent.MimeType"/> property.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? MimeType => message.MimeType;

    /// <summary>
    /// Converts a set of messages to <see cref="ChatMessageReference"/> instances.
    /// </summary>
    public static IEnumerable<ChatMessageReference> Prepare(IEnumerable<ChatMessageContent> messages) =>
        messages.Select(m => new ChatMessageReference(m));
}
