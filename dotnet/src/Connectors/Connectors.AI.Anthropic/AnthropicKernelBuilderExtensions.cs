// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure the Anthropic connector.
/// </summary>
public static class AnthropicKernelBuilderExtensions
{
    /// <summary>
    /// Adds the Anthropic completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="modelId">Anthropic model name; must be <c>claude-2</c> or <c>claude-instant-1</c>.</param>
    /// <param name="apiKey">Anthropic API key</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="alsoAsTextCompletion">Whether to use the service also for text completion, if supported</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAnthropicChatCompletionService(this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? serviceId = null,
        bool alsoAsTextCompletion = true,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        AnthropicChatCompletion Factory(ILoggerFactory loggerFactory, IDelegatingHandlerFactory httpHandlerFactory) => new(
            modelId,
            apiKey,
            HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
            loggerFactory
        );

        builder.WithAIService<IChatCompletion>(serviceId, Factory, setAsDefault);
        if (alsoAsTextCompletion)
        {
            builder.WithAIService<ITextCompletion>(serviceId, Factory, setAsDefault);
        }

        return builder;
    }
}
