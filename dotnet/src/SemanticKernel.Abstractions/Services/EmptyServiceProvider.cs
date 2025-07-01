// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
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
            return CreateArray(serviceType.GenericTypeArguments[0], 0);
        }

        return null;
    }

    [UnconditionalSuppressMessage("AotAnalysis", "IL3050:RequiresDynamicCode", Justification = "VerifyAotCompatibility ensures elementType is not a ValueType")]
    private static Array CreateArray(Type elementType, int length)
    {
        if (VerifyAotCompatibility && elementType.IsValueType)
        {
            // NativeAOT apps are not able to make Enumerable of ValueType services
            // since there is no guarantee the ValueType[] code has been generated.
            throw new InvalidOperationException($"Unable to create an Enumerable service of type '{elementType}' because it is a ValueType. Native code to support creating Enumerable services might not be available with native AOT.");
        }

        return Array.CreateInstance(elementType, length);
    }

    private static bool VerifyAotCompatibility =>
#if NET8_0_OR_GREATER
            !System.Runtime.CompilerServices.RuntimeFeature.IsDynamicCodeSupported;
#else
            false;
#endif
}
