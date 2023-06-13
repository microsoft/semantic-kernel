// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// Value of `Content` for a `ChatMessage` of type `ChatMessageType.Document`.
/// </summary>
public class DocumentMessageContent
{
    /// <summary>
    /// Name of the uploaded document.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Size of the uploaded document in bytes.
    /// </summary>
    [JsonPropertyName("size")]
    public string Size { get; set; } = string.Empty;

    /// <summary>
    /// Serialize the object to a JSON string.
    /// </summary>
    /// <returns>A serialized JSON string</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Deserialize a JSON string to a DocumentMessageContent object.
    /// </summary>
    /// <param name="json">A JSON string</param>
    /// <returns>A DocumentMessageContent object</returns>
    public static DocumentMessageContent? FromString(string json)
    {
        return JsonSerializer.Deserialize<DocumentMessageContent>(json);
    }
}
