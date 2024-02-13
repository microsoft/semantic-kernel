// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// list of run steps belonging to a run.
/// </summary>
internal sealed class AssistantListModel : OpenAIListModel<AssistantModel>
{
    // No specialization
}

/// <summary>
/// Model of Assistant data returned from OpenAI
/// </summary>
internal sealed record AssistantModel
{
    /// <summary>
    /// Identifier, which can be referenced in API endpoints
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// Unix timestamp (in seconds) for when the assistant was created
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; init; }

    /// <summary>
    /// Name of the assistant
    /// </summary>
    [JsonPropertyName("name")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; set; }

    /// <summary>
    /// The description of the assistant
    /// </summary>
    [JsonPropertyName("description")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; set; }

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
    public List<ToolModel> Tools { get; init; } = new List<ToolModel>();

    /// <summary>
    /// A list of file IDs attached to this assistant.
    /// There can be a maximum of 20 files attached to the assistant.
    /// </summary>
    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; init; } = new List<string>();

    /// <summary>
    /// Set of 16 key-value pairs that can be attached to an object.
    /// This can be useful for storing additional information about the
    /// object in a structured format.
    /// Keys can be a maximum of 64 characters long and values can be a
    /// maximum of 512 characters long.
    /// </summary>
    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; init; } = new Dictionary<string, object>();

    /// <summary>
    /// Assistant file model.
    /// </summary>
    public sealed class FileModel
    {
        /// <summary>
        /// ID of the assistant.
        /// </summary>
        [JsonPropertyName("assistant_id")]
        public string AssistantId { get; set; } = string.Empty;

        /// <summary>
        /// ID of the uploaded file.
        /// </summary>
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        /// <summary>
        /// Unix timestamp (in seconds) for when the assistant was created
        /// </summary>
        [JsonPropertyName("created_at")]
        public long CreatedAt { get; init; }
    }
}
