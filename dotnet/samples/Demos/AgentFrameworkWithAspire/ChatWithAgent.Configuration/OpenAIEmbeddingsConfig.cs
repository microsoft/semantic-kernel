// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ChatWithAgent.Configuration;

/// <summary>
/// OpenAI embeddings configuration.
/// </summary>
public sealed class OpenAIEmbeddingsConfig
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string ConfigSectionName = "OpenAIEmbeddings";

    /// <summary>
    /// The name of the embeddings model.
    /// </summary>
    [Required]
    public string ModelName { get; set; } = string.Empty;
}
