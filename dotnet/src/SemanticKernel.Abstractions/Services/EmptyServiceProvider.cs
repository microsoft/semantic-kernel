// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>Empty <see cref="IServiceProvider"/> implementation that returns null from all <see cref="IServiceProvider.GetService"/> calls.</summary>
internal sealed class EmptyServiceProvider : IServiceProvider, IKeyedServiceProvider
{
    /// <summary>Singleton instance of <see cref="EmptyServiceProvider"/>.</summary>
    public static IServiceProvider Instance { get; } = new EmptyServiceProvider();

    /// <inheritdoc/>
    public object? GetService(Type serviceType) => null;

    /// <inheritdoc/>
    public object? GetKeyedService(Type serviceType, object? serviceKey) => null;

    /// <inheritdoc/>
    public object GetRequiredKeyedService(Type serviceType, object? serviceKey) =>
        throw new InvalidOperationException(serviceKey is null ?
            $"No service for type '{serviceType}' has been registered." :
            $"No service for type '{serviceType}' and service key '{serviceKey}' has been registered.");
}
