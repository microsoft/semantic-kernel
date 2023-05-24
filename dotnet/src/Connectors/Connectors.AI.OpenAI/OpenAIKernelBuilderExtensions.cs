// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Reliability;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class OpenAIKernelBuilderExtensions
{
    #region Auto Configuration
    /// <summary>
    /// Adds all available Azure OpenAI model deployments to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceIdPrefix">Optional srting to prepend onto the model name when registering the service. Used to disambiguate, when multiple connectors
    /// may have the same model names. Example: specifying prefix "openai:" will result in model registrations of the form "openai:gpt-3.5-turbo".</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureOpenAI(this KernelBuilder builder,
        string endpoint,
        string apiKey,
        string? serviceIdPrefix = null,
        HttpClient? httpClient = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        // Get list of (available) models on Azure OpenAI instance
        var models = AzureOpenAIRestClient.GetModelsAsync(endpoint, apiKey, httpClient, cancellationToken).RunTaskSynchronously();

        // Get list of deployments
        var deployments = AzureOpenAIRestClient.GetDeploymentsAsync(endpoint, apiKey, httpClient, cancellationToken).RunTaskSynchronously();

        foreach (AzureDeploymentInfo d in deployments.Values)
        {
            AzureModelInfo model = models[d.Model];
            string serviceId = $"{serviceIdPrefix ?? string.Empty}{d.Model}";

            if (model.Capabilities.SupportsChatCompletion
                || model.Id.StartsWith("gpt-", StringComparison.OrdinalIgnoreCase))
            {
                builder.WithAzureChatCompletionService(
                    d.Id,
                    endpoint,
                    apiKey,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered Azure OpenAI chat completion model: {Model}, serviceId: {ServiceId}", d.Model, serviceId);
            }

            if (model.Capabilities.SupportsTextCompletion)
            {
                builder.WithAzureTextCompletionService(
                    d.Id,
                    endpoint,
                    apiKey,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered Azure OpenAI text completion model: {Model}, serviceId: {ServiceId}", d.Model, serviceId);
            }

            if (model.Capabilities.SupportsEmbeddings)
            {
                builder.WithAzureTextEmbeddingGenerationService(
                    d.Id,
                    endpoint,
                    apiKey,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered Azure OpenAI embedding generation model: {Model}, serviceId: {ServiceId}", d.Model, serviceId);
            }
        }

        return builder;
    }

    /// <summary>
    /// Adds all OpenAI model deployments to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="apiKey">OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="organization">OpenAI organization Id</param>
    /// <param name="serviceIdPrefix">Optional srting to prepend onto the model name when registering the service. Used to disambiguate, when multiple connectors
    /// may have the same model names. Example: specifying prefix "openai:" will result in model registrations of the form "openai:gpt-3.5-turbo".</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAI(this KernelBuilder builder,
        string apiKey,
        string? organization = null,
        string? serviceIdPrefix = null,
        HttpClient? httpClient = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        // Get list of (available) models on Azure OpenAI instance
        var models = OpenAIRestClient.GetModelsAsync(apiKey, organization, httpClient, cancellationToken).RunTaskSynchronously();

        foreach (var model in models.Values)
        {
            string serviceId = $"{serviceIdPrefix ?? string.Empty}{model.Id}";

            if (model.Capabilities.SupportsChatCompletion)
            {
                builder.WithOpenAIChatCompletionService(
                    model.Id,
                    apiKey,
                    organization,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered OpenAI chat completion model: {Model}, serviceId: {ServiceId}", model.Id, serviceId);
            }

            if (model.Capabilities.SupportsTextCompletion)
            {
                builder.WithOpenAITextCompletionService(
                    model.Id,
                    apiKey,
                    organization,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered OpenAI text completion model: {Model}, serviceId: {ServiceId}", model.Id, serviceId);
            }

            if (model.Capabilities.SupportsEmbeddings)
            {
                builder.WithOpenAITextEmbeddingGenerationService(
                    model.Id,
                    apiKey,
                    organization,
                    serviceId: serviceId,
                    httpClient: httpClient);

                logger?.LogInformation("Registered OpenAI embedding generation model: {Model}, serviceId: {ServiceId}", model.Id, serviceId);
            }
        }

        return builder;
    }
    #endregion

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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureTextCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (parameters) =>
            new AzureTextCompletion(
                deploymentName,
                endpoint,
                apiKey,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureTextCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (parameters) =>
            new AzureTextCompletion(
                deploymentName,
                endpoint,
                credentials,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAITextCompletionService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (parameters) =>
            new OpenAITextCompletion(
                modelId,
                apiKey,
                orgId,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureTextEmbeddingGenerationService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (parameters) =>
            new AzureTextEmbeddingGeneration(
                deploymentName,
                endpoint,
                apiKey,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureTextEmbeddingGenerationService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (parameters) =>
            new AzureTextEmbeddingGeneration(
                deploymentName,
                endpoint,
                credential,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAITextEmbeddingGenerationService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (parameters) =>
            new OpenAITextEmbeddingGeneration(
                modelId,
                apiKey,
                orgId,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        AzureChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters) => new(
            deploymentName,
            endpoint,
            apiKey,
            httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
            parameters.Logger);

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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        AzureChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters) => new(
            deploymentName,
            endpoint,
            credentials,
            httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
            parameters.Logger);

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
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAIChatCompletionService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool alsoAsTextCompletion = true,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        OpenAIChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters) => new(
            modelId,
            apiKey,
            orgId,
            httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
            parameters.Logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }

    private static HttpClient CreateHttpClient(this IDelegatingHandlerFactory handlerFactory, ILogger? logger)
    {
        var retryHandler = handlerFactory.Create(logger);
        retryHandler.InnerHandler = new HttpClientHandler { CheckCertificateRevocationList = true };
        return new HttpClient(retryHandler);
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
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAIImageGenerationService(this KernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<IImageGeneration>(serviceId, ((ILogger Logger, KernelConfig Config) parameters) =>
            new OpenAIImageGeneration(
                apiKey,
                orgId,
                httpClient ?? parameters.Config.HttpHandlerFactory.CreateHttpClient(parameters.Logger),
                parameters.Logger),
            setAsDefault);

        return builder;
    }

    #endregion
}
