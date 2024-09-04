// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IKernelBuilder"/> and related classes to configure AssemblyAI connectors.
/// </summary>
public static class AssemblyAIKernelBuilderExtensions
{
    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="apiKey">AssemblyAI API key, <a href="https://www.assemblyai.com/dashboard">get your API key from the dashboard.</a></param>
    /// <param name="endpoint">The endpoint URL to the AssemblyAI API.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAssemblyAIAudioToText(
        this IKernelBuilder builder,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null
    )
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, (serviceProvider, _)
            => new AssemblyAIAudioToTextService(
                apiKey,
                endpoint,
                httpClient));

        return builder;
    }
}
