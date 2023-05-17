// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

/// <summary>
/// A collection of semantic chat memory.
/// </summary>
public class SemanticChatMemory
{
    /// <summary>
    /// The chat memory items.
    /// </summary>
    [JsonPropertyName("items")]
    public List<SemanticChatMemoryItem> Items { get; set; } = new List<SemanticChatMemoryItem>();

    /// <summary>
    /// Create and add a chat memory item.
    /// </summary>
    /// <param name="label">Label for the chat memory item.</param>
    /// <param name="details">Details for the chat memory item.</param>
    public void AddItem(string label, string details)
    {
        this.Items.Add(new SemanticChatMemoryItem(label, details));
    }

    /// <summary>
    /// Serialize the chat memory to a Json string.
    /// </summary>
    /// <returns>A Json string representing the chat memory.</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Create a semantic chat memory from a Json string.
    /// </summary>
    /// <param name="json">Json string to deserialize.</param>
    /// <returns>A semantic chat memory.</returns>
    public static SemanticChatMemory FromJson(string json)
    {
        var result = JsonSerializer.Deserialize<SemanticChatMemory>(json);
        return result ?? throw new ArgumentException("Failed to deserialize chat memory to json.");
    }
}
