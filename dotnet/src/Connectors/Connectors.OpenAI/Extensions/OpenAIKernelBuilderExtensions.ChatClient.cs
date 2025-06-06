// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using OpenAI;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for <see cref="IKernelBuilder"/>.</summary>
[Experimental("SKEXP0010")]
public static class OpenAIChatClientKernelBuilderExtensions
{
    #region Chat Completion

    /// <summary>
    /// Adds an OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOpenAIChatClient(
            modelId,
            apiKey,
            orgId,
            serviceId,
            httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOpenAIChatClient(
            modelId,
            openAIClient,
            serviceId);

        return builder;
    }

    /// <summary>
    /// Adds a custom endpoint OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Custom OpenAI Compatible Message API endpoint</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        string? apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOpenAIChatClient(
            modelId,
            endpoint,
            apiKey,
            orgId,
            serviceId,
            httpClient);

        return builder;
    }

    #endregion
}
