// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Services;

public interface INamedServiceProvider
{
    /// <summary>
    /// Gets the service of the specified type and name, or null if not found.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <returns>The service instance, or null if not found.</returns>
    T? GetService<T>(string? name = null);

    /// <summary>
    /// Tries to get the service of the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="service">The output parameter to receive the service instance, or null if not found.</param>
    /// <returns>True if the service was found, false otherwise.</returns>
    bool TryGetService<T>([NotNullWhen(true)] out T? service);

    /// <summary>
    /// Tries to get the service of the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="service">The output parameter to receive the service instance, or null if not found.</param>
    /// <returns>True if the service was found, false otherwise.</returns>
    bool TryGetService<T>(string name, [NotNullWhen(true)] out T? service);

    /// <summary>
    /// Gets the names of all the registered services of the specified type, excluding the default service.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <returns>An enumerable of the service names.</returns>
    IEnumerable<string> GetServiceNames<T>();

    /// <summary>
    /// Gets the name of the default service for the specified type, or null if none.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <returns>The name of the default service, or null if none.</returns>
    public string? GetDefaultServiceName<T>();
}
