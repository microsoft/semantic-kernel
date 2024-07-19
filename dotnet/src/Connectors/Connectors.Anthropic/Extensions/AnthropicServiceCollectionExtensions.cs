// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Anthropic generation services to the application.
/// </summary>
public static class AnthropicServiceCollectionExtensions
{
    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Claude Text Generation service to.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        ClientOptions options)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(options.ServiceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return services;
    }
}
