// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Configuration;

namespace Microsoft.SemanticKernel.AI.OpenAI.Configuration;

public static class KernelConfigExtensions
{
    /// <summary>
    /// Adds an Azure OpenAI completion backend to the config.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="kernelConfig">Sponsored class instance reference</param>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureOpenAICompletionBackend(this KernelConfig kernelConfig,
        string label,
        string deploymentName,
        string endpoint,
        string apiKey,
        string apiVersion = AzureOpenAIConfig.SupportedVersion,
        bool overwrite = false)
    {
        var config = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        kernelConfig.AddCompletionBackendConfig(config, (logger) =>
            new AzureTextCompletion(
                config.DeploymentName,
                config.Endpoint,
                config.APIKey,
                config.APIVersion = AzureOpenAIConfig.SupportedVersion,
                logger
            ), overwrite);

        return kernelConfig;
    }

    /// <summary>
    /// Adds an Azure OpenAI embeddings backend to the config.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="kernelConfig">Sponsored class instance reference</param>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureOpenAIEmbeddingsBackend(this KernelConfig kernelConfig,
        string label,
        string deploymentName,
        string endpoint,
        string apiKey,
        string apiVersion = AzureOpenAIConfig.SupportedVersion,
        bool overwrite = false)
    {
        var config = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        kernelConfig.AddEmbeddingsBackendConfig(config, overwrite);

        return kernelConfig;
    }

    /// <summary>
    /// Adds the OpenAI completion backend to the config.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="kernelConfig">Sponsored class instance reference</param>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAICompletionBackend(this KernelConfig kernelConfig,
        string label,
        string modelId,
        string apiKey,
        string? orgId = null,
        bool overwrite = false)
    {
        var config = new OpenAIConfig(label, modelId, apiKey, orgId);

        kernelConfig.AddCompletionBackendConfig(config, (logger) =>
            new OpenAITextCompletion(
                config.ModelId,
                config.APIKey,
                config.OrgId,
                logger
            ), overwrite);

        return kernelConfig;
    }

    /// <summary>
    /// Adds the OpenAI embeddings backend to the config.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="kernelConfig">Sponsored class instance reference</param>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIEmbeddingsBackend(this KernelConfig kernelConfig,
        string label,
        string modelId,
        string apiKey,
        string? orgId = null,
        bool overwrite = false)
    {
        var config = new OpenAIConfig(label, modelId, apiKey, orgId);

        kernelConfig.AddEmbeddingsBackendConfig(config, overwrite);

        return kernelConfig;
    }
}
