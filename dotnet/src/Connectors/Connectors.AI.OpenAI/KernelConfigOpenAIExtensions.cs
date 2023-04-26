// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;

public static class KernelConfigOpenAIExtensions
{
    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="services">The services instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureTextCompletionService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, string apiKey)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(INamedServiceProvider sp) => new AzureTextCompletion(
            deploymentName, endpoint, apiKey, sp.GetHttpRetryHandler(), sp.GetLogger<ITextCompletion>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureTextCompletionService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(INamedServiceProvider sp) => new AzureTextCompletion(
            deploymentName, endpoint, credentials, sp.GetHttpRetryHandler(), sp.GetLogger<ITextCompletion>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI text completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddOpenAITextCompletionService(this INamedServiceCollection services,
        string serviceId, string modelId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(INamedServiceProvider sp) => new OpenAITextCompletion(
            modelId, apiKey, orgId, sp.GetHttpRetryHandler(), sp.GetLogger<ITextCompletion>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureTextEmbeddingGenerationService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, string apiKey)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextEmbeddingGeneration Factory(INamedServiceProvider sp) => new AzureTextEmbeddingGeneration(
            deploymentName, endpoint, apiKey, sp.GetHttpRetryHandler(), sp.GetLogger<ITextCompletion>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureTextEmbeddingService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextEmbeddingGeneration Factory(INamedServiceProvider sp) => new AzureTextEmbeddingGeneration(
            deploymentName, endpoint, credentials, sp.GetHttpRetryHandler(), sp.GetLogger<ITextCompletion>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddOpenAITextEmbeddingGenerationService(this INamedServiceCollection services,
        string serviceId, string modelId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextEmbeddingGeneration Factory(INamedServiceProvider sp) => new OpenAITextEmbeddingGeneration(
            modelId, apiKey, orgId, sp.GetHttpRetryHandler(), sp.GetLogger<OpenAITextEmbeddingGeneration>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureChatCompletionService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, string apiKey, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        AzureChatCompletion Factory(INamedServiceProvider sp) => new(
            deploymentName, endpoint, apiKey, sp.GetHttpRetryHandler(), sp.GetLogger<AzureChatCompletion>());

        services.SetServiceFactory<IChatCompletionService>(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            services.SetServiceFactory<ITextCompletion>(serviceId, Factory);
        }

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddAzureChatCompletionService(this INamedServiceCollection services,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        AzureChatCompletion Factory(INamedServiceProvider sp) => new(
            deploymentName, endpoint, credentials, sp.GetHttpRetryHandler(), sp.GetLogger<AzureChatCompletion>());

        services.SetServiceFactory<IChatCompletionService>(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            services.SetServiceFactory<ITextCompletion>(serviceId, Factory);
        }

        return services;
    }

    /// <summary>
    /// Adds the OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddOpenAIChatCompletionService(this INamedServiceCollection services,
        string serviceId, string modelId, string apiKey, string? orgId = null, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        OpenAIChatCompletion Factory(INamedServiceProvider sp) => new(
            modelId, apiKey, orgId, sp.GetHttpRetryHandler(), sp.GetLogger<OpenAIChatCompletion>());

        services.SetServiceFactory<IChatCompletionService>(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
        {
            services.SetServiceFactory<ITextCompletion>(serviceId, Factory);
        }

        return services;
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="services">The service collection instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <returns>Self instance</returns>
    public static INamedServiceCollection AddOpenAIImageGenerationService(this INamedServiceCollection services,
        string serviceId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IImageGeneration Factory(INamedServiceProvider sp) => new OpenAIImageGeneration(
            apiKey, orgId, sp.GetHttpRetryHandler(), sp.GetLogger<OpenAIImageGeneration>());

        services.SetServiceFactory(serviceId, Factory);

        return services;
    }

    #endregion
}
