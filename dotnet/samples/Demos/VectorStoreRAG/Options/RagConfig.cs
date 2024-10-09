// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Contains settings to control the RAG experience.
/// </summary>
internal sealed class RagConfig
{
    public const string ConfigSectionName = "Rag";

    [Required]
    public bool BuildCollection { get; set; } = true;

    [Required]
    public string[]? PdfFilePaths { get; set; }

    [Required]
    public string VectorStoreType { get; set; } = string.Empty;

    [Required]
    public string CollectionName { get; set; } = string.Empty;
}
