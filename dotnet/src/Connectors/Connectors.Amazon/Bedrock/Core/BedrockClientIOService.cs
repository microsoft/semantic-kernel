// Copyright (c) Microsoft. All rights reserved.

using Connectors.Amazon.Models;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Cohere;
using Connectors.Amazon.Models.Meta;
using Connectors.Amazon.Models.Mistral;

namespace Connectors.Amazon.Bedrock.Core;

/// <summary>
/// Utilities to get the model IO service and model provider. Used by Bedrock service clients.
/// </summary>
public class BedrockClientIOService
{
    /// <summary>
    /// Gets the model IO service for body conversion.
    /// </summary>
    /// <param name="modelId"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public IBedrockModelIOService GetIOService(string modelId)
    {
        string[] parts = modelId.Split('.'); //modelId looks like "amazon.titan-text-premier-v1:0"
        string modelProvider = parts[0];
        string modelName = parts.Length > 1 ? parts[1] : string.Empty;

        switch (modelProvider)
        {
            case "ai21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JambaIOService();
                }
                if (modelName.StartsWith("j2-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AI21JurassicIOService();
                }
                throw new ArgumentException($"Unsupported AI21 model: {modelId}");
            case "amazon":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AmazonIOService();
                }
                throw new ArgumentException($"Unsupported Amazon model: {modelId}");
            case "anthropic":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    return new AnthropicIOService();
                }
                throw new ArgumentException($"Unsupported Anthropic model: {modelId}");
            case "cohere":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandRIOService();
                }
                if (modelName.StartsWith("command-", StringComparison.OrdinalIgnoreCase))
                {
                    return new CohereCommandIOService();
                }
                throw new ArgumentException($"Unsupported Cohere model: {modelId}");
            case "meta":
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MetaIOService();
                }
                throw new ArgumentException($"Unsupported Meta model: {modelId}");
            case "mistral":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralIOService();
                }
                if (modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    return new MistralIOService();
                }
                throw new ArgumentException($"Unsupported Mistral model: {modelId}");
            default:
                throw new ArgumentException($"Unsupported model provider: {modelProvider}");
        }
    }
    /// <summary>
    /// Gets the model provider from modelId.
    /// </summary>
    /// <param name="modelId"></param>
    /// <returns></returns>
    public string GetModelProvider(string modelId)
    {
        string[] parts = modelId.Split('.'); //modelId looks like "amazon.titan-text-premier-v1:0"
        return parts[0];
    }
}
