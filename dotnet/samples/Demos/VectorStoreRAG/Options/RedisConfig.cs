// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Redis service settings.
/// </summary>
internal sealed class RedisConfig
{
    public const string ConfigSectionName = "Redis";

    [Required]
    public string ConnectionConfiguration { get; set; } = string.Empty;
}
