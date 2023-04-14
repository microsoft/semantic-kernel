// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// A single entry in the chat memory.
/// </summary>
public class SemanticChatMemoryItem
{
    /// <summary>
    /// Label for the chat memory item.
    /// </summary>
    [JsonPropertyName("label")]
    public string Label { get; set; }

    /// <summary>
    /// Details for the chat memory item.
    /// </summary>
    [JsonPropertyName("details")]
    public string Details { get; set; }

    public SemanticChatMemoryItem(string label, string details)
    {
        this.Label = label;
        this.Details = details;
    }

    public string ToFormattedString()
    {
        return $"{this.Label}: {this.Details}";
    }
}

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
    public void AddItem(string label, string details)
    {
        this.Items.Add(new SemanticChatMemoryItem(label, details));
    }

    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Create a chat memory from string.
    /// </summary>
    public static SemanticChatMemory FromJson(string json)
    {
        var result = JsonSerializer.Deserialize<SemanticChatMemory>(json);
        if (result == null)
        {
            throw new Exception("Failed to deserialize chat memory to json.");
        }
        return result;
    }
}