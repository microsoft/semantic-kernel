// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Present a <see cref="ChatMessageForPrompt"/> for serialization without metadata.
/// </summary>
/// <param name="message">The referenced message</param>
internal sealed class ChatMessageForPrompt(ChatMessageContent message)
{
    private static readonly JsonSerializerOptions s_jsonOptions = new() { WriteIndented = true };

    /// <summary>
    /// The string representation of the <see cref="ChatMessageContent.Role"/> property.
    /// </summary>
    public string Role => message.Role.Label;

    /// <summary>
    /// The referenced <see cref="ChatMessageContent.AuthorName"/> property.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name => message.AuthorName;

    /// <summary>
    /// The referenced <see cref="ChatMessageContent.Content"/> property.
    /// </summary>
    public string Content => message.Content ?? string.Empty;

    /// <summary>
    /// Convenience method to reference a set of messages.
    /// </summary>
    public static IEnumerable<ChatMessageForPrompt> Prepare(IEnumerable<ChatMessageContent> messages) =>
        messages.Where(m => !string.IsNullOrWhiteSpace(m.Content)).Select(m => new ChatMessageForPrompt(m));

    /// <summary>
    /// Convenience method to format a set of messages for use in a prompt.
    /// </summary>
    public static string Format(IEnumerable<ChatMessageContent> messages) =>
        JsonSerializer.Serialize(Prepare(messages).ToArray(), s_jsonOptions);
}
