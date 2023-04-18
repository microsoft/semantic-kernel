// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration settings for the memories store.
/// </summary>
public class MemoriesStoreConfig
{
    /// <summary>
    /// The type of memories store to use.
    /// </summary>
    public enum MemoriesStoreType
    {
        /// <summary>
        /// Non-persistent memories store.
        /// </summary>
        Volatile,

        /// <summary>
        /// Qdrant based persistent memories store.
        /// </summary>
        Qdrant
    }

    /// <summary>
    /// Gets or sets the type of memories store to use.
    /// </summary>
    public MemoriesStoreType Type { get; set; } = MemoriesStoreType.Volatile;

    /// <summary>
    /// Gets or sets the configuration for the Qdrant memories store.
    /// </summary>
    public QdrantConfig? Qdrant { get; set; }
}
