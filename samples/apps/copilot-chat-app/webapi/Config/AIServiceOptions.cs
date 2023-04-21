// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

public sealed class AIServiceOptions
{
    public const string CompletionPropertyName = "Completion";
    public const string EmbeddingPropertyName = "Embedding";

    public enum AIServiceType
    {
        AzureOpenAI,
        OpenAI
    }

    [Required]
    public string Label { get; set; } = string.Empty;

    [Required]
    public AIServiceType AIService { get; set; }

    [Required]
    public string DeploymentOrModelId { get; set; } = string.Empty;
    
    public string Endpoint { get; set; } = string.Empty;

    [Required]
    public string Key { get; set; } = string.Empty;

    // TODO support OpenAI's orgID 
}
