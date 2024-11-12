﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.Inference;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure Azure AI Inference connectors.
/// </summary>
public static class AzureAIInferenceServiceCollectionExtensions
{
    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(
        this IServiceCollection services,
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var chatClientBuilder = new ChatClientBuilder()
               .UseFunctionInvocation(config =>
                   config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<ChatCompletionsClient>();
            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            var options = new AzureAIInferenceClientOptions();
            if (httpClient is not null)
            {
                options.Transport = new HttpClientTransport(HttpClientProvider.GetHttpClient(httpClient, serviceProvider));
            }

            return
                chatClientBuilder.Use(
                    new Microsoft.Extensions.AI.AzureAIInferenceChatClient(
                        modelId: modelId,
                        chatCompletionsClient: new Azure.AI.Inference.ChatCompletionsClient(endpoint, new Azure.AzureKeyCredential(apiKey ?? SingleSpace), options)
                    )
                ).AsChatCompletionService();
        });

        return services;
    }

    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(
        this IServiceCollection services,
        string modelId,
        TokenCredential credential,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var chatClientBuilder = new ChatClientBuilder()
               .UseFunctionInvocation(config =>
                   config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<ChatCompletionsClient>();
            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            var options = new AzureAIInferenceClientOptions();
            if (httpClient is not null)
            {
                options.Transport = new HttpClientTransport(HttpClientProvider.GetHttpClient(httpClient, serviceProvider));
            }

            return
                chatClientBuilder.Use(
                    new Microsoft.Extensions.AI.AzureAIInferenceChatClient(
                        modelId: modelId,
                        chatCompletionsClient: new Azure.AI.Inference.ChatCompletionsClient(endpoint, credential, options)
                    )
                ).AsChatCompletionService();
        });

        return services;
    }

    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Azure AI Inference model id</param>
    /// <param name="chatClient"><see cref="ChatCompletionsClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(this IServiceCollection services,
        string modelId,
        ChatCompletionsClient? chatClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            chatClient ??= serviceProvider.GetRequiredService<ChatCompletionsClient>();

            var chatClientBuilder = new ChatClientBuilder()
               .UseFunctionInvocation(config =>
                   config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<ChatCompletionsClient>();
            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            return chatClientBuilder
                .Use(new Microsoft.Extensions.AI.AzureAIInferenceChatClient(chatClient, modelId))
                .AsChatCompletionService();
        });

        return services;
    }

    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="chatClient"><see cref="AzureAIInferenceChatClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(this IServiceCollection services,
        AzureAIInferenceChatClient? chatClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            chatClient ??= serviceProvider.GetRequiredService<AzureAIInferenceChatClient>();

            var chatClientBuilder = new ChatClientBuilder()
               .UseFunctionInvocation(config =>
                   config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<ChatCompletionsClient>();
            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            return chatClientBuilder
                .Use(chatClient)
                .AsChatCompletionService();
        });

        return services;
    }

    #region Private

    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertize itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 128;

    /// <summary>
    /// When using Azure AI Inference against Gateway APIs that don't require an API key,
    /// this single space is used to avoid breaking the client.
    /// </summary>
    private const string SingleSpace = " ";

    #endregion
}
