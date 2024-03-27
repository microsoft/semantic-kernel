// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Extension methods for interacting with <see cref="SemanticTextMemory"/>.
/// </summary>
public static class SemanticTextMemoryExtensions
{
    /// <summary>
    /// Adds the SemanticTextMemory service to the specified <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to add the service to.</param>
    /// <returns>A <see cref="MemoryBuilder"/> instance.</returns>
    public static MemoryBuilder AddSemanticTextMemory(this IServiceCollection services)
    {
        Verify.NotNull(services, nameof(services));

        services.AddTransient<ISemanticTextMemory, SemanticTextMemory>();

        return new MemoryBuilder(services);
    }
}
