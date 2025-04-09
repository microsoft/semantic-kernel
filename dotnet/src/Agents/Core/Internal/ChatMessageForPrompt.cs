// Copyright (c) Microsoft. All rights reserved.
using System;
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
#pragma warning disable SKEXP0001
    public string? Name => message.AuthorName;
#pragma warning restore SKEXP0001

    /// <summary>
    /// The referenced <see cref="ChatMessageContent.Content"/> property.
    /// </summary>
    public string Content => message.Content ?? string.Empty;

    /// <summary>
    /// Convenience method to format a set of messages for use in a prompt.
    /// </summary>
    public static string Format(IEnumerable<ChatMessageContent> messages, bool useNameOnly = false) =>
        useNameOnly ?
            JsonSerializer.Serialize(Prepare(messages, m => string.IsNullOrEmpty(m.AuthorName) ? m.Role.Label : m.AuthorName).ToArray(), s_jsonOptions) :
            JsonSerializer.Serialize(Prepare(messages, m => new ChatMessageForPrompt(m)).ToArray(), s_jsonOptions);

    /// <summary>
    /// Convenience method to reference a set of messages.
    /// </summary>
    internal static IEnumerable<TResult> Prepare<TResult>(IEnumerable<ChatMessageContent> messages, Func<ChatMessageContent, TResult> transform) =>
        messages.Where(m => !string.IsNullOrWhiteSpace(m.Content)).Select(m => transform.Invoke(m));
}
