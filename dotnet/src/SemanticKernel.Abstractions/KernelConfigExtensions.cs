// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for extension methods for <see cref="KernelConfig"/> class.
/// </summary>
public static class KernelConfigExtensions
{
    /// <summary>
    /// Returns service factory from <see cref="KernelConfig"/> service collection.
    /// </summary>
    /// <param name="serviceCollection">Service collection in <see cref="KernelConfig"/>.</param>
    /// <param name="name">Name of service.</param>
    public static Func<IKernel, T> GetServiceFactory<T>(this Dictionary<string, Func<IKernel, T>> serviceCollection, string? name)
    {
        name ??= KernelConfig.DefaultServiceId;

        if (!serviceCollection.TryGetValue(name, out Func<IKernel, T> factory))
        {
            throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, $"'{name}' service not available");
        }

        return factory;
    }
}
