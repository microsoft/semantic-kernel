// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Anthropic generation services to the application.
/// </summary>
public static class AnthropicKernelBuilderExtensions
{
    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        ClientOptions options,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(options.ServiceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }
}
