// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration settings for connecting to Qdrant.
/// </summary>
public class QdrantConfig
{
    /// <summary>
    /// Gets or sets the endpoint protocol and host (e.g. http://localhost).
    /// </summary>
    public string Host { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the endpoint port.
    /// </summary>
    public int Port { get; set; }

    /// <summary>
    /// Gets or sets the vector size.
    /// </summary>
    public int VectorSize { get; set; }
}
