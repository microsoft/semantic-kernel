// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for AI services, such as Azure OpenAI and OpenAI.
/// </summary>
public sealed class AIServiceOptions
{
    public const string CompletionPropertyName = "Completion";
    public const string EmbeddingPropertyName = "Embedding";

    public enum AIServiceType
    {
        AzureOpenAI,
        OpenAI
    }

    /// <summary>
    /// Label used for referencing the AI service in Semantic Kernel.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Label { get; set; } = string.Empty;

    /// <summary>
    /// Type of AI service.
    /// </summary>
    [Required]
    public AIServiceType AIService { get; set; } = AIServiceType.AzureOpenAI;

    /// <summary>
    /// Azure OpenAI deployment name or OpenAI model name.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string DeploymentOrModelId { get; set; } = string.Empty;

    /// <summary>
    /// (Azure OpenAI only) Azure OpenAI endpoint.
    /// </summary>
    [RequiredOnPropertyValue(nameof(AIService), AIServiceType.AzureOpenAI, notEmptyOrWhitespace: true)]
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Key to access the AI service.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;

    // TODO support OpenAI's orgID
}
