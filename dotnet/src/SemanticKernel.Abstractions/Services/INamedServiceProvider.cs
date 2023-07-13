// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

public interface INamedServiceProvider<in TService>
{
    /// <summary>
    /// Gets the service of the specified type and name, or null if not found.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <returns>The service instance, or null if not found.</returns>
    T? GetService<T>(string? name = null) where T : TService;
}
