// Copyright (c) Microsoft.All rights reserved.

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration settings for connecting to Weaviate.
/// </summary>
public class WeaviateOptions
{
    /// <summary>
    /// Gets or sets the scheme (e.g. http or https).
    /// </summary>
    public string Scheme { get; set; } = "http";
    
    /// <summary>
    /// Gets or sets the endpoint protocol and host (e.g. http://localhost).
    /// </summary>
    public string Host { get; set; } = string.Empty;
    
    /// <summary>
    /// Gets or sets the api key.
    /// </summary>
    public string ApiKey { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the endpoint port.
    /// </summary>
    public int Port { get; set; }
}
