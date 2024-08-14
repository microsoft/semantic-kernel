// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Utilities to get the model IO service and model provider. Used by Bedrock service clients.
/// </summary>
internal sealed class BedrockClientIOService
{
    /// <summary>
    /// Gets the model IO service for body conversion.
    /// </summary>
    /// <param name="modelId">The model to be used for the IO service.</param>
    /// <returns><see cref="IBedrockTextGenerationIOService"/> object</returns>
    /// <exception cref="NotSupportedException">Thrown if model does not support text generation.</exception>
    internal IBedrockTextGenerationIOService GetTextIOService(string modelId)
    {
        (string modelProvider, string modelName) = this.GetModelProviderAndName(modelId);

        switch (modelProvider.ToUpperInvariant())
        {
            case "AI21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JambaIOService();
                }
                if (modelName.StartsWith("j2-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JurassicIOService();
                }
                throw new NotSupportedException($"Unsupported AI21 model: {modelId}");
            case "AMAZON":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonIOService();
                }
                throw new NotSupportedException($"Unsupported Amazon model: {modelId}");
            case "ANTHROPIC":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AnthropicIOService();
                }
                throw new NotSupportedException($"Unsupported Anthropic model: {modelId}");
            case "COHERE":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandRIOService();
                }
                if (modelName.StartsWith("command-", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandIOService();
                }
                throw new NotSupportedException($"Unsupported Cohere model: {modelId}");
            case "META":
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MetaIOService();
                }
                throw new NotSupportedException($"Unsupported Meta model: {modelId}");
            case "MISTRAL":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase)
                    || modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralIOService();
                }
                throw new NotSupportedException($"Unsupported Mistral model: {modelId}");
            default:
                throw new NotSupportedException($"Unsupported model provider: {modelProvider}");
        }
    }

    /// <summary>
    /// Gets the model IO service for body conversion.
    /// </summary>
    /// <param name="modelId">The model to get the IO service for.</param>
    /// <returns><see cref="IBedrockChatCompletionIOService"/> object</returns>
    /// <exception cref="NotSupportedException">Thrown if that model does not support chat completion.</exception>
    internal IBedrockChatCompletionIOService GetChatIOService(string modelId)
    {
        (string modelProvider, string modelName) = this.GetModelProviderAndName(modelId);

        switch (modelProvider.ToUpperInvariant())
        {
            case "AI21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JambaIOService();
                }
                throw new NotSupportedException($"Unsupported AI21 model: {modelId}");
            case "AMAZON":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonIOService();
                }
                throw new NotSupportedException($"Unsupported Amazon model: {modelId}");
            case "ANTHROPIC":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AnthropicIOService();
                }
                throw new NotSupportedException($"Unsupported Anthropic model: {modelId}");
            case "COHERE":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandRIOService();
                }
                throw new NotSupportedException($"Unsupported Cohere model: {modelId}");
            case "META":
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MetaIOService();
                }
                throw new NotSupportedException($"Unsupported Meta model: {modelId}");
            case "MISTRAL":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase)
                    || modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralIOService();
                }
                throw new NotSupportedException($"Unsupported Mistral model: {modelId}");
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
