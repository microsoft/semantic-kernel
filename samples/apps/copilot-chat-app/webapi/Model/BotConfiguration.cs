// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Model;

public class BotConfiguration
{
    /// <summary>
    /// The AI service
    /// </summary>
    public string EmbeddingAIService { get; set; } = string.Empty;

    /// <summary>
    /// The deployment or the model id
    /// </summary>
    public string EmbeddingDeploymentOrModelId { get; set; } = string.Empty;
}
