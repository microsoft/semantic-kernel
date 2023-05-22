// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureRestApi;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.OpenAIRestApi;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Reliability;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class KernelConfigOpenAIExtensions
{
    /// <summary>
    /// Adds all available Azure OpenAI model deployments to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Self instance</returns>
    public static async Task<KernelConfig> AddAzureOpenAIAsync(this KernelConfig config,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        // Get list of (available) models on Azure OpenAI instance
        var models = await AzureOpenAIRestClient.GetModelsAsync(endpoint, apiKey, httpClient, cancellationToken).ConfigureAwait(false);

        // Get list of deployments
        var deployments = await AzureOpenAIRestClient.GetDeploymentsAsync(endpoint, apiKey, httpClient, cancellationToken).ConfigureAwait(false);

        foreach (AzureDeployment d in deployments.Values)
        {
            AzureModel model = models[d.Model];
            if (model.Capabilities.SupportsTextCompletion)
            {
                config.AddAzureTextCompletionService(
                    d.Id,
                    endpoint,
                    apiKey,
                    serviceId: d.Model,
                    httpClient: httpClient,
                    logger: logger);
            }

            if (model.Capabilities.SupportsEmbeddings)
            {
                config.AddAzureTextEmbeddingGenerationService(
                    d.Id,
                    endpoint,
                    apiKey,
                    serviceId: d.Model,
                    httpClient: httpClient,
                    logger: logger);
            }
        }

        return config;
    }

    /// <summary>
    /// Adds all OpenAI model deployments to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="apiKey">OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="organization">OpenAI organization Id</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Self instance</returns>
    public static async Task<KernelConfig> AddOpenAIAsync(this KernelConfig config,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        // Get list of (available) models on Azure OpenAI instance
        var models = await OpenAIRestClient.GetModelsAsync(apiKey, organization, httpClient, cancellationToken).ConfigureAwait(false);

        foreach (var model in models.Values)
        {
            if (model.Capabilities.SupportsTextCompletion)
            {
                config.AddOpenAITextCompletionService(
                    d.Id,
                    apiKey,
                    serviceId: d.Model,
                    httpClient: httpClient,
                    logger: logger);
            }

            if (model.Capabilities.SupportsEmbeddings)
            {
                config.AddAzureTextEmbeddingGenerationService(
                    d.Id,
                    apiKey,
                    serviceId: d.Model,
                    httpClient: httpClient,
                    logger: logger);
            }
        }

        return config;
    }

    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureTextCompletionService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        ITextCompletion Factory(IKernel kernel) => new AzureTextCompletion(
            deploymentName,
            endpoint,
            apiKey,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextCompletionService(Factory, serviceId);

        return config;
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureTextCompletionService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        ITextCompletion Factory(IKernel kernel) => new AzureTextCompletion(
            deploymentName,
            endpoint,
            credentials,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextCompletionService(Factory, serviceId);

        return config;
    }

    /// <summary>
    /// Adds the OpenAI text completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddOpenAITextCompletionService(this KernelConfig config,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        ITextCompletion Factory(IKernel kernel) => new OpenAITextCompletion(
            modelId,
            apiKey,
            orgId,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextCompletionService(Factory, serviceId);

        return config;
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureTextEmbeddingGenerationService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new AzureTextEmbeddingGeneration(
            deploymentName,
            endpoint,
            apiKey,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextEmbeddingGenerationService(Factory, serviceId);

        return config;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureTextEmbeddingGenerationService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new AzureTextEmbeddingGeneration(
            deploymentName,
            endpoint,
            credentials,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextEmbeddingGenerationService(Factory, serviceId);

        return config;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddOpenAITextEmbeddingGenerationService(this KernelConfig config,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new OpenAITextEmbeddingGeneration(
            modelId,
            apiKey,
            orgId,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddTextEmbeddingGenerationService(Factory, serviceId);

        return config;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureChatCompletionService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        string apiKey,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IChatCompletion Factory(IKernel kernel) => new AzureChatCompletion(
            deploymentName, endpoint, apiKey, kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log), kernel.Log);

        config.AddChatCompletionService(Factory, serviceId);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new AzureChatCompletion(
                deploymentName,
                endpoint,
                apiKey,
                httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
                logger ?? kernel.Log);

            config.AddTextCompletionService(TextServiceFactory, serviceId);
        }

        return config;
    }

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddAzureChatCompletionService(this KernelConfig config,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IChatCompletion Factory(IKernel kernel) => new AzureChatCompletion(
            deploymentName,
            endpoint,
            credentials,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddChatCompletionService(Factory, serviceId);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new AzureChatCompletion(
                deploymentName,
                endpoint,
                credentials,
                httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
                logger ?? kernel.Log);

            config.AddTextCompletionService(TextServiceFactory, serviceId);
        }

        return config;
    }

    /// <summary>
    /// Adds the OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddOpenAIChatCompletionService(this KernelConfig config,
        string modelId,
        string apiKey,
        string? orgId = null,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IChatCompletion Factory(IKernel kernel) => new OpenAIChatCompletion(
            modelId,
            apiKey,
            orgId,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddChatCompletionService(Factory, serviceId);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new OpenAIChatCompletion(
                modelId,
                apiKey,
                orgId,
                httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
                logger ?? kernel.Log);

            config.AddTextCompletionService(TextServiceFactory, serviceId);
        }

        return config;
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use the corresponding extension method in the KernelBuilder class instead.")]
    public static KernelConfig AddOpenAIImageGenerationService(this KernelConfig config,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        IImageGeneration Factory(IKernel kernel) => new OpenAIImageGeneration(
            apiKey,
            orgId,
            httpClient ?? kernel.Config.HttpHandlerFactory.CreateHttpClient(kernel.Log),
            logger ?? kernel.Log);

        config.AddImageGenerationService(Factory, serviceId);

        return config;
    }

    #endregion

    private static HttpClient CreateHttpClient(this IDelegatingHandlerFactory handlerFactory,
        ILogger? logger)
    {
        var retryHandler = handlerFactory.Create(logger);
        retryHandler.InnerHandler = new HttpClientHandler { CheckCertificateRevocationList = true };
        return new HttpClient(retryHandler);
    }
}
