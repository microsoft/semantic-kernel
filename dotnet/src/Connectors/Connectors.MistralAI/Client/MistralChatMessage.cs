// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Chat message for MistralAI.
/// </summary>
internal sealed class MistralChatMessage
{
    [JsonPropertyName("role")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Role { get; set; }

    [JsonPropertyName("content")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Content { get; set; }

    [JsonPropertyName("name")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; set; }

    [JsonPropertyName("tool_call_id")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ToolCallId { get; set; }

    [JsonPropertyName("tool_calls")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<MistralToolCall>? ToolCalls { get; set; }

    /// <summary>
    /// Construct an instance of <see cref="MistralChatMessage"/>.
    /// </summary>
    /// <param name="role">If provided must be one of: system, user, assistant</param>
    /// <param name="content">Content of the chat message</param>
    [JsonConstructor]
    internal MistralChatMessage(string? role, object? content)
    {
        if (role is not null and not "system" and not "user" and not "assistant" and not "tool")
        {
            throw new System.ArgumentException($"Role must be one of: system, user, assistant or tool. {role} is an invalid role.", nameof(role));
        }

        this.Role = role;
        this.Content = content;
    }
}
