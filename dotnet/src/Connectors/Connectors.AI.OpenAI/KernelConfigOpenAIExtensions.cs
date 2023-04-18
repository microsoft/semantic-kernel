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

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;

public static class KernelConfigOpenAIExtensions
{
    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureTextCompletionService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, string apiKey)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(IKernel kernel) => new AzureTextCompletion(
            deploymentName, endpoint, apiKey, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextCompletionService(serviceId, Factory);

        return config;
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureTextCompletionService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(IKernel kernel) => new AzureTextCompletion(
            deploymentName, endpoint, credentials, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextCompletionService(serviceId, Factory);

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
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAITextCompletionService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        ITextCompletion Factory(IKernel kernel) => new OpenAITextCompletion(
            modelId, apiKey, orgId, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextCompletionService(serviceId, Factory);

        return config;
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureTextEmbeddingGenerationService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, string apiKey)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new AzureTextEmbeddingGeneration(
            deploymentName, endpoint, apiKey, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextEmbeddingGenerationService(serviceId, Factory);

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
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureTextEmbeddingGenerationService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new AzureTextEmbeddingGeneration(
            deploymentName, endpoint, credentials, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextEmbeddingGenerationService(serviceId, Factory);

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
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAITextEmbeddingGenerationService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IEmbeddingGeneration<string, float> Factory(IKernel kernel) => new OpenAITextEmbeddingGeneration(
            modelId, apiKey, orgId, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddTextEmbeddingGenerationService(serviceId, Factory);

        return config;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureChatCompletionService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, string apiKey, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IChatCompletion Factory(IKernel kernel) => new AzureChatCompletion(
            deploymentName, endpoint, apiKey, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddChatCompletionService(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new AzureChatCompletion(
                deploymentName, endpoint, apiKey, kernel.Config.HttpHandlerFactory, kernel.Log);

            config.AddTextCompletionService(serviceId, TextServiceFactory);
        }

        return config;
    }

    /// <summary>
    /// Adds the Azure OpenAI ChatGPT completion service to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddAzureChatCompletionService(this KernelConfig config,
        string serviceId, string deploymentName, string endpoint, TokenCredential credentials, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IChatCompletion Factory(IKernel kernel) => new AzureChatCompletion(
            deploymentName, endpoint, credentials, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddChatCompletionService(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(AzureChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new AzureChatCompletion(
                deploymentName, endpoint, credentials, kernel.Config.HttpHandlerFactory, kernel.Log);

            config.AddTextCompletionService(serviceId, TextServiceFactory);
        }

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
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIChatCompletionService(this KernelConfig config,
        string serviceId, string modelId, string apiKey, string? orgId = null, bool alsoAsTextCompletion = true)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IChatCompletion Factory(IKernel kernel) => new OpenAIChatCompletion(
            modelId, apiKey, orgId, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddChatCompletionService(serviceId, Factory);

        // If the class implements the text completion interface, allow to use it also for semantic functions
        if (alsoAsTextCompletion && typeof(ITextCompletion).IsAssignableFrom(typeof(OpenAIChatCompletion)))
        {
            ITextCompletion TextServiceFactory(IKernel kernel) => new OpenAIChatCompletion(
                modelId, apiKey, orgId, kernel.Config.HttpHandlerFactory, kernel.Log);

            config.AddTextCompletionService(serviceId, TextServiceFactory);
        }

        return config;
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="config">The kernel config instance</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <returns>Self instance</returns>
    public static KernelConfig AddOpenAIImageGenerationService(this KernelConfig config,
        string serviceId, string apiKey, string? orgId = null)
    {
        Verify.NotEmpty(serviceId, "The service Id provided is empty");

        IImageGeneration Factory(IKernel kernel) => new OpenAIImageGeneration(
            apiKey, orgId, kernel.Config.HttpHandlerFactory, kernel.Log);

        config.AddImageGenerationService(serviceId, Factory);

        return config;
    }

    #endregion
}
