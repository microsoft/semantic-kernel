// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

/// <summary>
/// Model of Assistant data returned from OpenAI
/// </summary>
public class AssistantModel
{
    /// <summary>
    /// Identifier, which can be referenced in API endpoints
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Always "assistant"
    /// </summary>
    [JsonPropertyName("object")]
    public string Object { get; set; } = "assistant";

    /// <summary>
    /// Unix timestamp (in seconds) for when the assistant was created
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// Name of the assistant
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The description of the assistant
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// ID of the model to use
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    /// <summary>
    /// The system instructions that the assistant uses
    /// </summary>
    [JsonPropertyName("instructions")]
    public string Instructions { get; set; } = string.Empty;

    /// <summary>
    /// A list of tool enabled on the assistant
    /// There can be a maximum of 128 tools per assistant.
    /// </summary>
    [JsonPropertyName("tools")]
    public List<ToolModel> Tools { get; set; }

    /// <summary>
    /// A list of file IDs attached to this assistant.
    /// There can be a maximum of 20 files attached to the assistant.
    /// </summary>
    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; set; }

    /// <summary>
    /// Set of 16 key-value pairs that can be attached to an object.
    /// This can be useful for storing additional information about the
    /// object in a structured format.
    /// Keys can be a maximum of 64 characters long and values can be a
    /// maxium of 512 characters long.
    /// </summary>
    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; }

    /// <summary>
    /// Tool entry
    /// </summary>
    public class ToolModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;
    }
}
