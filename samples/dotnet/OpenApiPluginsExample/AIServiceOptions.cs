// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace OpenApiPluginsExample;

/// <summary>
/// Configuration options for AI services, such as Azure OpenAI and OpenAI.
/// </summary>
public sealed class AIServiceOptions
{
    public const string PropertyName = "AIService";

    /// <summary>
    /// Supported types of AI services.
    /// </summary>
    public enum AIServiceType
    {
        /// <summary>
        /// Azure OpenAI https://learn.microsoft.com/en-us/azure/cognitive-services/openai/
        /// </summary>
        AzureOpenAI,

        /// <summary>
        /// OpenAI https://openai.com/
        /// </summary>
        OpenAI
    }

    /// <summary>
    /// AI models to use.
    /// </summary>
    public class ModelTypes
    {
        /// <summary>
        /// Azure OpenAI deployment name or OpenAI model name to use for completions.
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string Completion { get; set; } = string.Empty;
    }

    /// <summary>
    /// Type of AI service.
    /// </summary>
    [Required]
    public AIServiceType Type { get; set; } = AIServiceType.AzureOpenAI;

    /// <summary>
    /// Models/deployment names to use.
    /// </summary>
    [Required]
    public ModelTypes Models { get; set; } = new ModelTypes();

    /// <summary>
    /// (Azure OpenAI only) Azure OpenAI endpoint.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), AIServiceType.AzureOpenAI, notEmptyOrWhitespace: true)]
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Token limits for completion model interactions.
    /// </summary>
    [Required]
    public int TokenLimit { get; set; } = 4096;

    /// <summary>
    /// Key to access the AI service.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;
}
