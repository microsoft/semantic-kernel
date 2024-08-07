// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// Metadata for a file in the session.
/// </summary>
public class SessionsRemoteFileMetadata
{
    /// <summary>
    /// Initializes a new instance of the SessionRemoteFileMetadata class.
    /// </summary>
    [JsonConstructor]
    public SessionsRemoteFileMetadata(string filename, int size)
    {
        this.Filename = filename;
        this.Size = size;
    }

    /// <summary>
    /// The filename relative to `/mnt/data`.
    /// </summary>
    [Description("The filename relative to `/mnt/data`.")]
    [JsonPropertyName("filename")]
    public string Filename { get; set; }

    /// <summary>
    /// The size of the file in bytes.
    /// </summary>
    [Description("The size of the file in bytes.")]
    [JsonPropertyName("size")]
    public int Size { get; set; }

    /// <summary>
    /// The last modified time.
    /// </summary>
    [Description("Last modified time.")]
    [JsonPropertyName("lastModifiedTime")]
    public DateTime? LastModifiedTime { get; set; }

    /// <summary>
    /// The full path of the file.
    /// </summary>
    [Description("The full path of the file.")]
    public string FullPath => $"/mnt/data/{this.Filename}";
}
