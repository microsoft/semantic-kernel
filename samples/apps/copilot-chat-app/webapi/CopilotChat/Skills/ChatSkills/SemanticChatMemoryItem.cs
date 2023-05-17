// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

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

    /// <summary>
    /// Create a new chat memory item.
    /// </summary>
    /// <param name="label">Label of the item.</param>
    /// <param name="details">Details of the item.</param>
    public SemanticChatMemoryItem(string label, string details)
    {
        this.Label = label;
        this.Details = details;
    }

    /// <summary>
    /// Format the chat memory item as a string.
    /// </summary>
    /// <returns>A formatted string representing the item.</returns>
    public string ToFormattedString()
    {
        return $"{this.Label}: {this.Details}";
    }
}
