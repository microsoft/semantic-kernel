// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

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

        /// <summary>
        /// Azure OpenAI deployment name or OpenAI model name to use for embeddings.
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string Embedding { get; set; } = string.Empty;

        /// <summary>
        /// Azure OpenAI deployment name or OpenAI model name to use for planner.
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string Planner { get; set; } = string.Empty;

        /// <summary>
        /// Specific endpoint for planner if needed
        /// </summary>
        public string PlannerEndpoint { get; set; } = string.Empty;

        /// <summary>
        /// Specific key for planner if needed
        /// </summary>
        public string PlannerKey { get; set; } = string.Empty;
    }
"AIService": {
    "Type": "AzureOpenAI",
    "Endpoint": "", // ignored when AIService is "OpenAI"
    // "Key": "",
    "Models": {
      "Completion": "gpt-35-turbo", // For OpenAI, change to 'gpt-3.5-turbo' (with a period).
      "Embedding": "text-embedding-ada-002",
    },
    "PlannerOverrides": {
        // Planner will default to the same settings for the Chat Completion model set above
        // Set below properties if you want to use a different chat completion model or Azure OpenAI endpoint for the Planner, otherwise, leave as is
        "Model": "", 
        "Endpoint": "",
        // - Set "Key" using dotnet's user secrets (i.e. dotnet user-secrets set "AIService:PlannerOverrides:Key" "MY_AZURE_OPENAI_KEY")
        "Key": "" // Required if you want to use a different endpoint for the planner
    }
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
    /// Key to access the AI service.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Key { get; set; } = string.Empty;
}
