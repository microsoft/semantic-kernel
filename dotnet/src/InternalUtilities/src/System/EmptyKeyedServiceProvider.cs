// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>Provides an implementation of <see cref="IKeyedServiceProvider"/> that contains no services.</summary>
internal sealed class EmptyKeyedServiceProvider : IKeyedServiceProvider
{
    /// <summary>Gets a singleton instance of <see cref="EmptyKeyedServiceProvider"/>.</summary>
    public static EmptyKeyedServiceProvider Instance { get; } = new();

    /// <inheritdoc />
    public object? GetService(Type serviceType) => null;

    /// <inheritdoc />
    public object? GetKeyedService(Type serviceType, object? serviceKey) => null;

    /// <inheritdoc />
    public object GetRequiredKeyedService(Type serviceType, object? serviceKey) =>
        this.GetKeyedService(serviceType, serviceKey) ??
        throw new InvalidOperationException($"No service for type '{serviceType}' and key '{serviceKey}' has been registered.");
}
