// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.Inference;
using Azure.Core;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IKernelBuilder"/> to configure Azure AI Inference connectors.
/// </summary>
public static class AzureAIInferenceKernelBuilderExtensions
{
    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureAIInferenceChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureAIInferenceChatCompletion(modelId, apiKey, endpoint, httpClient, serviceId);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureAIInferenceChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        TokenCredential credential,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureAIInferenceChatCompletion(modelId, credential, endpoint, httpClient, serviceId);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">Azure AI Inference model id</param>
    /// <param name="chatClient"><see cref="ChatCompletionsClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureAIInferenceChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        ChatCompletionsClient? chatClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureAIInferenceChatCompletion(modelId, chatClient, serviceId);

        return builder;
    }
}
