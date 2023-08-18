// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Reliability;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure OpenAI and AzureOpenAI connectors.
/// </summary>
public static class OpenAIKernelBuilderExtensions
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
        {
            var client = CreateAzureOpenAIClient(parameters.Logger, parameters.Config, deploymentName, endpoint, new AzureKeyCredential(apiKey), httpClient);
            return new AzureTextCompletion(deploymentName, client, parameters.Logger);
        }, setAsDefault);

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
        {
            var client = CreateAzureOpenAIClient(parameters.Logger, parameters.Config, deploymentName, endpoint, credentials, httpClient);
            return new AzureTextCompletion(deploymentName, client, parameters.Logger);
        }, setAsDefault);

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureTextCompletionService(this KernelBuilder builder,
        string deploymentName,
        OpenAIClient openAIClient,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (parameters) =>
            new AzureTextCompletion(
                deploymentName,
                openAIClient,
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
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
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
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
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
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
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
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
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
        AzureChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters)
        {
            OpenAIClient client = CreateAzureOpenAIClient(parameters.Logger, parameters.Config, deploymentName, endpoint, new AzureKeyCredential(apiKey), httpClient);

            return new(deploymentName, client, parameters.Logger);
        };

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
        AzureChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters)
        {
            OpenAIClient client = CreateAzureOpenAIClient(parameters.Logger, parameters.Config, deploymentName, endpoint, credentials, httpClient);

            return new(deploymentName, client, parameters.Logger);
        };

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI chat completion with data.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureChatCompletionService(this KernelBuilder builder,
        AzureChatCompletionWithDataConfig config,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        AzureChatCompletionWithData Factory((ILogger Logger, KernelConfig Config) parameters) => new(
            config,
            HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
            parameters.Logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletionWithData)))
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
            HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
            parameters.Logger);

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
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
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        OpenAIClient openAIClient,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        AzureChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters)
        {
            return new(deploymentName, openAIClient, parameters.Logger);
        };

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
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithOpenAIChatCompletionService(this KernelBuilder builder,
        string deploymentName,
        OpenAIClient openAIClient,
        bool alsoAsTextCompletion = true,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        OpenAIChatCompletion Factory((ILogger Logger, KernelConfig Config) parameters)
        {
            return new(deploymentName, openAIClient, parameters.Logger);
        };

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
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
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
                parameters.Logger),
            setAsDefault);

        return builder;
    }

    /// <summary>
    /// Add the  Azure OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="maxRetryCount">Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureOpenAIImageGenerationService(this KernelBuilder builder,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null,
        int maxRetryCount = 5)
    {
        builder.WithAIService<IImageGeneration>(serviceId, ((ILogger Logger, KernelConfig Config) parameters) =>
            new AzureOpenAIImageGeneration(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
                parameters.Logger,
                maxRetryCount),
            setAsDefault);

        return builder;
    }

    #endregion

    private static OpenAIClient CreateAzureOpenAIClient(ILogger logger, KernelConfig config, string deploymentName, string endpoint, AzureKeyCredential credentials, HttpClient? httpClient)
    {
        OpenAIClientOptions options = CreateOpenAIClientOptions(logger, config, httpClient);

        return new(new Uri(endpoint), credentials, options);
    }

    private static OpenAIClient CreateAzureOpenAIClient(ILogger logger, KernelConfig config, string deploymentName, string endpoint, TokenCredential credentials, HttpClient? httpClient)
    {
        OpenAIClientOptions options = CreateOpenAIClientOptions(logger, config, httpClient);

        return new(new Uri(endpoint), credentials, options);
    }

    private static OpenAIClientOptions CreateOpenAIClientOptions(ILogger logger, KernelConfig config, HttpClient? httpClient)
    {
        OpenAIClientOptions options = new();
#pragma warning disable CA2000 // Dispose objects before losing scope
        options.Transport = new HttpClientTransport(HttpClientProvider.GetHttpClient(config, httpClient, logger));
#pragma warning restore CA2000 // Dispose objects before losing scope

        if (config.HttpHandlerFactory is DefaultHttpRetryHandlerFactory factory && factory.Config is not null)
        {
            options.Retry.MaxRetries = factory.Config.MaxRetryCount;
            options.Retry.MaxDelay = factory.Config.MaxRetryDelay;
        }

        return options;
    }
}
