// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Model;

/// <summary>
/// The embedding configuration of a bot. Used in the Bot object for portability.
/// </summary>
public class BotEmbeddingConfig
{
    /// <summary>
    /// The AI service.
    /// </summary>
    public string AIService { get; set; } = string.Empty;

    /// <summary>
    /// The deployment or the model id.
    /// </summary>
    public string DeploymentOrModelId { get; set; } = string.Empty;
}
