// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Milvus service settings.
/// </summary>
internal sealed class MilvusConfig
{
    public const string ConfigSectionName = "Milvus";

    [Required]
    public string Host { get; set; } = string.Empty;

    public int Port { get; set; } = 19530;

    public bool Https { get; set; } = true;

    public string? ApiKey { get; set; }

    public string? Database { get; set; }
}
