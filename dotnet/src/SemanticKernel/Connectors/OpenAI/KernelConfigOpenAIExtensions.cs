// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;

public static class KernelConfigOpenAIExtensions
{
    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same id exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureOpenAITextCompletionService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, string apiKey, string apiVersion = "2022-12-01", bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.TextCompletionServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"A text completion service with id '{serviceId}' already exists");
        }

        ITextCompletion Factory(KernelConfig config) => new AzureTextCompletion(
            deploymentName, endpoint, apiKey, apiVersion, config.LoggerFactory, config.HttpClientFactory);

        config.AddTextCompletionService(serviceId, Factory, overwrite);

        return config;
    }

    /// <summary>
    /// Adds the OpenAI text completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAITextCompletionService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.TextCompletionServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"A text completion service with the id '{serviceId}' already exists");
        }



        ITextCompletion Factory(KernelConfig config) => new OpenAITextCompletion(
            modelId, apiKey, orgId, config.LoggerFactory, config.HttpClientFactory);

        config.AddTextCompletionService(serviceId, Factory, overwrite);

        return config;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same id exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureOpenAIEmbeddingGenerationService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, string apiKey, string apiVersion = "2022-12-01", bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.TextEmbeddingGenerationServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"A text embedding service with the id '{serviceId}' already exists");
        }

        IEmbeddingGeneration<string, float> Factory(KernelConfig config) => new AzureTextEmbeddingGeneration(
            deploymentName, endpoint, apiKey, apiVersion, config.LoggerFactory, config.HttpClientFactory);

        config.AddTextEmbeddingGenerationService(serviceId, Factory, overwrite);

        return config;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same id exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIEmbeddingGenerationService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.TextEmbeddingGenerationServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"A text embedding service with the id '{serviceId}' already exists");
        }

        IEmbeddingGeneration<string, float> Factory(KernelConfig config) => new OpenAITextEmbeddingGeneration(
            modelId, apiKey, orgId, config.LoggerFactory, config.HttpClientFactory);

        config.AddTextEmbeddingGenerationService(serviceId, Factory, overwrite);

        return config;
    }

    /// <summary>
    /// Adds the OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIChatCompletionService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.ChatCompletionServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"A chat completion service with the id '{serviceId}' already exists");
        }

        IChatCompletion Factory(KernelConfig config) => new OpenAIChatCompletion(
            modelId, apiKey, orgId, config.LoggerFactory, config.HttpClientFactory);

        config.AddChatCompletionService(serviceId, Factory, overwrite);

        return config;
    }

    /// <summary>
    /// Add the OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIImageGenerationService(this KernelConfig config,
        string serviceId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        if (!overwrite && config.ImageGenerationServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"An image generation service with the id '{serviceId}' already exists");
        }

        IImageGeneration Factory(KernelConfig config) => new OpenAIImageGeneration(
            apiKey, orgId, config.LoggerFactory, config.HttpClientFactory);

        config.AddImageGenerationService(serviceId, Factory, overwrite);

        return config;
    }
}
