// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// Metadata for an entity: file or directory in the session.
/// </summary>
public sealed class SessionsRemoteFileMetadata
{
    /// <summary>
    /// The name of the entity.
    /// </summary>
    [Description("The name of the entity.")]
    [JsonPropertyName("name")]
    public required string Name { get; set; }

    /// <summary>
    /// The size of the entity in bytes.
    /// </summary>
    [Description("The size of the entity in bytes.")]
    [JsonPropertyName("sizeInBytes")]
    public int? SizeInBytes { get; set; }

    /// <summary>
    /// The entity last modified time.
    /// </summary>
    [Description("The entity last modified time.")]
    [JsonPropertyName("lastModifiedAt")]
    public required DateTime LastModifiedAt { get; set; }

    /// <summary>
    /// The type of the entity content.
    /// </summary>
    [Description("The type of the entity content.")]
    [JsonPropertyName("contentType")]
    public string? ContentType { get; set; }

    /// <summary>
    /// Specifies the type of the entity. Can be either `file` or `directory`.
    /// </summary>
    [Description("The type of the entity.")]
    [JsonPropertyName("type")]
    public required string Type { get; set; }

    /// <summary>
    /// The full path of the entity.
    /// </summary>
    [Description("The full path of the entity.")]
    public string FullPath => $"/mnt/data/{this.Name}";
}
