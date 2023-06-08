// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration settings for the memories store.
/// </summary>
public class MemoriesStoreOptions
{
    public const string PropertyName = "MemoriesStore";

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
        Qdrant,

        /// <summary>
        /// Azure Cognitive Search persistent memories store.
        /// </summary>
        AzureCognitiveSearch
    }

    /// <summary>
    /// Gets or sets the type of memories store to use.
    /// </summary>
    public MemoriesStoreType Type { get; set; } = MemoriesStoreType.Volatile;

    /// <summary>
    /// Gets or sets the configuration for the Qdrant memories store.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), MemoriesStoreType.Qdrant)]
    public QdrantOptions? Qdrant { get; set; }

    /// <summary>
    /// Gets or sets the configuration for the Azure Cognitive Search memories store.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), MemoriesStoreType.AzureCognitiveSearch)]
    public AzureCognitiveSearchOptions? AzureCognitiveSearch { get; set; }
}
