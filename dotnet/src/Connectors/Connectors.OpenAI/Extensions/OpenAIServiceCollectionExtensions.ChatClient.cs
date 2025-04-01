// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel;

#pragma warning disable IDE0039 // Use local function

/// <summary>
/// Sponsor extensions class for <see cref="IServiceCollection"/>.
/// </summary>
public static class OpenAIChatClientServiceCollectionExtensions
{
    #region Chat Completion

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            ILogger? logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<OpenAIChatClient>();

            return new Microsoft.Extensions.AI.OpenAIChatClient(
                openAIClient: new OpenAIClient(new ApiKeyCredential(apiKey ?? SingleSpace), options: GetClientOptions(orgId: orgId, httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider))),
                modelId: modelId)
                .AsKernelFunctionInvokingChatClient(logger);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            ILogger? logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<OpenAIChatClient>();

            return new Microsoft.Extensions.AI.OpenAIChatClient(
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId)
                .AsKernelFunctionInvokingChatClient(logger);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    /// <summary>
    /// Adds the Custom OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">A Custom Message API compatible endpoint.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? apiKey = null,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            ILogger? logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger<OpenAIChatClient>();

            return new Microsoft.Extensions.AI.OpenAIChatClient(
                openAIClient: new OpenAIClient(new ApiKeyCredential(apiKey ?? SingleSpace), GetClientOptions(endpoint, orgId, HttpClientProvider.GetHttpClient(httpClient, serviceProvider))),
                modelId: modelId)
                .AsKernelFunctionInvokingChatClient(logger);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    private static OpenAIClientOptions GetClientOptions(
        Uri? endpoint = null,
        string? orgId = null,
        HttpClient? httpClient = null)
    {
        OpenAIClientOptions options = new();

        if (endpoint is not null)
        {
            options.Endpoint = endpoint;
        }

        if (orgId is not null)
        {
            options.OrganizationId = orgId;
        }

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
        }

        return options;
    }

    /// <summary>
    /// White space constant.
    /// </summary>
    private const string SingleSpace = " ";
    #endregion
}
