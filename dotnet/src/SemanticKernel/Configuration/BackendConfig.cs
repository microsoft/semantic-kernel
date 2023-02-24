// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.OpenAI.Services;

namespace Microsoft.SemanticKernel.Configuration;

/// <summary>
/// Backend configuration.
/// </summary>
public sealed class BackendConfig
{
    /// <summary>
    /// Backend type.
    /// </summary>
    public BackendTypes BackendType { get; set; } = BackendTypes.Unknown;

    /// <summary>
    /// Azure OpenAI configuration.
    /// </summary>
    public AzureOpenAIConfig? AzureOpenAI { get; set; } = null;

    /// <summary>
    /// OpenAI configuration.
    /// </summary>
    public OpenAIConfig? OpenAI { get; set; } = null;
}
