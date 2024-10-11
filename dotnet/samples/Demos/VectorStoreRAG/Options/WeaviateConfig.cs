// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Weaviate service settings.
/// </summary>
internal sealed class WeaviateConfig
{
    public const string ConfigSectionName = "Weaviate";

    [Required]
    public string Endpoint { get; set; } = string.Empty;
}
