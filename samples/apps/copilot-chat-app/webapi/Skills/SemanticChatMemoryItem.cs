// Copyright (c) Microsoft. All rights reserved.

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