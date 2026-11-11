// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Chroma service settings.
/// </summary>
internal sealed class ChromaConfig
{
    public const string ConfigSectionName = "Chroma";

    [Required]
    public string ConnectionString { get; set; } = string.Empty;
}
