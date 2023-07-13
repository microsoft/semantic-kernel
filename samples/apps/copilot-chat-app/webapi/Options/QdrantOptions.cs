// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration settings for connecting to Qdrant.
/// </summary>
public class QdrantOptions
{
    /// <summary>
    /// Gets or sets the endpoint protocol and host (e.g. http://localhost).
    /// </summary>
    [Required, Url]
    public string Host { get; set; } = string.Empty; // TODO update to use System.Uri

    /// <summary>
    /// Gets or sets the endpoint port.
    /// </summary>
    [Required, Range(0, 65535)]
    public int Port { get; set; }

    /// <summary>
    /// Gets or sets the vector size.
    /// </summary>
    [Required, Range(1, int.MaxValue)]
    public int VectorSize { get; set; }

    /// <summary>
    /// Gets or sets the Qdrant Cloud "api-key" header value.
    /// </summary>
    public string Key { get; set; } = string.Empty;
}
