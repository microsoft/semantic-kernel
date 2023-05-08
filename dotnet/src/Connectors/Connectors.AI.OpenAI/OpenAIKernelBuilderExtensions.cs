// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class OpenAKernelBuilderExtensions
{
    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureTextCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, () =>
            new AzureTextCompletion(
                deploymentName,
                endpoint,
                apiKey,
                httpClient,
                logger),
            setAsDefault);

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureTextCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, () =>
            new AzureTextCompletion(
                deploymentName,
                endpoint,
                credentials,
                httpClient,
                logger),
            setAsDefault);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddOpenAITextCompletionService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, () =>
            new OpenAITextCompletion(
                modelId,
                apiKey,
                orgId,
                httpClient,
                logger),
            setAsDefault);
        return builder;
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureTextEmbeddingGenerationService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, () =>
            new AzureTextEmbeddingGeneration(
                deploymentName,
                endpoint,
                apiKey,
                httpClient,
                logger),
            setAsDefault);
        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureTextEmbeddingGenerationService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, () =>
            new AzureTextEmbeddingGeneration(
                deploymentName,
                endpoint,
                credential,
                httpClient,
                logger),
            setAsDefault);
        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddOpenAITextEmbeddingGenerationService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, () =>
            new OpenAITextEmbeddingGeneration(
                modelId,
                apiKey,
                orgId,
                httpClient,
                logger),
            setAsDefault);
        return builder;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        AzureChatCompletion Factory() => new AzureChatCompletion(
            deploymentName,
            endpoint,
            apiKey,
            httpClient,
            logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddAzureChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        AzureChatCompletion Factory() => new AzureChatCompletion(
            deploymentName,
            endpoint,
            credentials,
            httpClient,
            logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddOpenAIChatCompletionService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool alsoAsTextCompletion = true,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        OpenAIChatCompletion Factory() => new OpenAIChatCompletion(
            modelId,
            apiKey,
            orgId,
            httpClient,
            logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder AddOpenAIImageGenerationService(this KernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        builder.WithAIService(serviceId, () =>
            new OpenAIImageGeneration(
                apiKey,
                orgId,
                httpClient,
                logger),
            setAsDefault);

        return builder;
    }

    #endregion
}
