// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Factory class for creating services for different models, providers and modalities.
/// </summary>
internal sealed class BedrockServiceFactory
{
    /// <summary>
    /// Represents an array of region prefixes used to identify different cross-region configurations
    /// for service operations. The prefixes correspond to general geographic areas such as
    /// "us" (United States), "eu" (Europe), and "apac" (Asia-Pacific).
    /// (sourced from https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
    /// </summary>
    private static readonly string[] s_crossRegionPrefixes = ["us.", "eu.", "apac."];

    /// <summary>
    /// Removes the cross-region prefix from the provided model identifier if it exists.
    /// </summary>
    /// <param name="modelId">The model identifier, which may contain a cross-region prefix.</param>
    /// <returns>The model identifier without the cross-region prefix.</returns>
    private static string ScrubCrossRegionPrefix(string modelId)
    {
        var prefix = s_crossRegionPrefixes.FirstOrDefault(prefix => modelId.StartsWith(prefix, StringComparison.InvariantCultureIgnoreCase));
        if (!string.IsNullOrWhiteSpace(prefix))
        {
            modelId = modelId.Substring(prefix.Length);
        }

        return modelId;
    }

    /// <summary>
    /// Gets the model service for body conversion.
    /// </summary>
    /// <param name="modelId">The model to be used for the service.</param>
    /// <returns><see cref="IBedrockTextGenerationService"/> instance</returns>
    /// <exception cref="NotSupportedException">Thrown if provider or model is not supported for text generation.</exception>
    internal IBedrockTextGenerationService CreateTextGenerationService(string modelId)
    {
        (string modelProvider, string modelName) = this.GetModelProviderAndName(ScrubCrossRegionPrefix(modelId));

        switch (modelProvider.ToUpperInvariant())
        {
            case "AI21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JambaService();
                }
                if (modelName.StartsWith("j2-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JurassicService();
                }
                throw new NotSupportedException($"Unsupported AI21 model: {modelId}");
            case "AMAZON":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonService();
                }
                throw new NotSupportedException($"Unsupported Amazon model: {modelId}");
            case "ANTHROPIC":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AnthropicService();
                }
                throw new NotSupportedException($"Unsupported Anthropic model: {modelId}");
            case "COHERE":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandRService();
                }
                if (modelName.StartsWith("command-", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandService();
                }
                throw new NotSupportedException($"Unsupported Cohere model: {modelId}");
            case "META":
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MetaService();
                }
                throw new NotSupportedException($"Unsupported Meta model: {modelId}");
            case "MISTRAL":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase)
                    || modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralService();
                }
                throw new NotSupportedException($"Unsupported Mistral model: {modelId}");
            default:
                throw new NotSupportedException($"Unsupported model provider: {modelProvider}");
        }
    }

    /// <summary>
    /// Gets the model service for body conversion.
    /// </summary>
    /// <param name="modelId">The model to get the service for.</param>
    /// <returns><see cref="IBedrockChatCompletionService"/> object</returns>
    /// <exception cref="NotSupportedException">Thrown if provider or model is not supported for chat completion.</exception>
    internal IBedrockChatCompletionService CreateChatCompletionService(string modelId)
    {
        (string modelProvider, string modelName) = this.GetModelProviderAndName(ScrubCrossRegionPrefix(modelId));

        switch (modelProvider.ToUpperInvariant())
        {
            case "AI21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JambaService();
                }
                throw new NotSupportedException($"Unsupported AI21 model: {modelId}");
            case "AMAZON":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonService();
                }
                throw new NotSupportedException($"Unsupported Amazon model: {modelId}");
            case "ANTHROPIC":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AnthropicService();
                }
                throw new NotSupportedException($"Unsupported Anthropic model: {modelId}");
            case "COHERE":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandRService();
                }
                throw new NotSupportedException($"Unsupported Cohere model: {modelId}");
            case "META":
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MetaService();
                }
                throw new NotSupportedException($"Unsupported Meta model: {modelId}");
            case "MISTRAL":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase)
                    || modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralService();
                }
                throw new NotSupportedException($"Unsupported Mistral model: {modelId}");
            default:
                throw new NotSupportedException($"Unsupported model provider: {modelProvider}");
        }
    }

    /// <summary>
    /// Gets the model service for body conversion.
    /// </summary>
    /// <param name="modelId">The model to get the service for.</param>
    /// <returns><see cref="IBedrockCommonTextEmbeddingGenerationService"/> object</returns>
    /// <exception cref="NotSupportedException">Thrown if provider or model is not supported for text embedding generation.</exception>
    internal IBedrockCommonTextEmbeddingGenerationService CreateTextEmbeddingService(string modelId)
    {
        (string modelProvider, string modelName) = this.GetModelProviderAndName(modelId);

        switch (modelProvider.ToUpperInvariant())
        {
            case "AMAZON":
                if (modelName.StartsWith("titan-embed-text", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonEmbedGenerationService();
                }
                throw new NotSupportedException($"Unsupported Amazon model: {modelId}");
            case "COHERE":
                if (modelName.StartsWith("embed-", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereEmbedGenerationService();
                }
                throw new NotSupportedException($"Unsupported Cohere model: {modelId}");
            default:
                throw new NotSupportedException($"Unsupported model provider: {modelProvider}");
        }
    }

    internal (string modelProvider, string modelName) GetModelProviderAndName(string modelId)
    {
        string[] parts = modelId.Split('.'); //modelId looks like "amazon.titan-text-premier-v1:0"
        string modelName = parts.Length > 1 ? parts[1].ToUpperInvariant() : string.Empty;
        return (parts[0], modelName);
    }
}
