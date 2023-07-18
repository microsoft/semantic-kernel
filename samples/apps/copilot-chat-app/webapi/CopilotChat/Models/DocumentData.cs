// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Models;

public sealed class DocumentData
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
    /// Status of the uploaded document.
    /// If true, the document is successfully uploaded. False otherwise.
    /// </summary>
    [JsonPropertyName("isUploaded")]
    public bool IsUploaded { get; set; } = false;
}
