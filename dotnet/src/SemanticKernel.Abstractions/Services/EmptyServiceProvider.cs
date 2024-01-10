// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>Empty <see cref="IServiceProvider"/> implementation that returns null from all <see cref="IServiceProvider.GetService"/> calls.</summary>
internal sealed class EmptyServiceProvider : IServiceProvider, IKeyedServiceProvider
{
    private static readonly ConcurrentDictionary<Type, object?> s_results = new();

    /// <summary>Singleton instance of <see cref="EmptyServiceProvider"/>.</summary>
    public static IServiceProvider Instance { get; } = new EmptyServiceProvider();

    /// <inheritdoc/>
    public object? GetService(Type serviceType) => s_results.GetOrAdd(serviceType, GetEmpty);

    /// <inheritdoc/>
    public object? GetKeyedService(Type serviceType, object? serviceKey) => s_results.GetOrAdd(serviceType, GetEmpty);

    /// <inheritdoc/>
    public object GetRequiredKeyedService(Type serviceType, object? serviceKey) =>
        throw new InvalidOperationException(serviceKey is null ?
            $"No service for type '{serviceType}' has been registered." :
            $"No service for type '{serviceType}' and service key '{serviceKey}' has been registered.");

    private static object? GetEmpty(Type serviceType)
    {
        if (serviceType.IsConstructedGenericType &&
            serviceType.GetGenericTypeDefinition() == typeof(IEnumerable<>))
        {
            return Array.CreateInstance(serviceType.GenericTypeArguments[0], 0);
        }

        return null;
    }
}
