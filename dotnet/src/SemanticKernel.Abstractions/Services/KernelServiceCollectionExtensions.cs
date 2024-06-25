// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>Extension methods for interacting with <see cref="Kernel"/>.</summary>
public static class KernelServiceCollectionExtensions
{
    /// <summary>Adds a <see cref="KernelPluginCollection"/> and <see cref="Kernel"/> services to the services collection.</summary>
    /// <param name="services">The service collection.</param>
    /// <returns>
    /// A <see cref="IKernelBuilder"/> that can be used to add additional services to the same <see cref="IServiceCollection"/>.
    /// </returns>
    /// <remarks>
    /// Both services are registered as transient, as both objects are mutable.
    /// </remarks>
    public static IKernelBuilder AddKernel(this IServiceCollection services)
    {
        Verify.NotNull(services);

        // Register a KernelPluginCollection to be populated with any IKernelPlugins that have been
        // directly registered in DI. It's transient because the Kernel will store the collection
        // directly, and we don't want two Kernel instances to hold on to the same mutable collection.
        services.AddTransient<KernelPluginCollection>();

        // Register the Kernel as transient. It's mutable and expected to be mutated by consumers,
        // such as via adding event handlers, adding plugins, storing state in its Data collection, etc.
        services.AddTransient<Kernel>();

        // Create and return a builder that can be used for adding services and plugins
        // to the IServiceCollection.
        return new KernelBuilder(services);
    }
}
