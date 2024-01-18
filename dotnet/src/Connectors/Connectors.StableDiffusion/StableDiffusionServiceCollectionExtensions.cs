// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI.ImageToImage;
using Microsoft.SemanticKernel.Connectors.StableDiffusion.ImageToImage;

namespace Microsoft.SemanticKernel.Connectors.StableDiffusion;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> and related classes to configure Stable Diffusion connectors.
/// </summary>
public static class StableDiffusionServiceCollectionExtensions
{
    /// <summary>
    /// Add Stable Diffusion image to image service to kernel
    /// </summary>
    public static IKernelBuilder AddStableDiffusionImageToImage(
        this IKernelBuilder builder,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<IImageToImageService>(serviceId, (serviceProvider, _) =>
        {
            return new StableDiffusionImageToImageService(apiKey, httpClient);
        });

        return builder;
    }

    /// <summary>
    /// Add Stable Diffusion image to image service to service collection
    /// </summary>
    public static IServiceCollection AddStableDiffusionImageToImage(
        this IServiceCollection services,
        string apiKey,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IImageToImageService>(serviceId, (serviceProvider, _) =>
        {
            return new StableDiffusionImageToImageService(apiKey);
        });
    }
}
