// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Services;
internal static class AIServiceProviderExtensions
{
    /// <summary>
    /// Get the service matching the given id or the default if an id is not provided or not found.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="serviceProvider">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The service matching the given id, the default service, or null.</returns>
    public static T? GetNamedServiceOrDefault<T>(
        this IAIServiceProvider serviceProvider,
        string? serviceId = null) where T : IAIService
    {
        if ((serviceId != null)
            && serviceProvider.TryGetService<T>(serviceId, out var namedService))
        {
            return namedService;
        }

        return serviceProvider.GetService<T>();
    }


    /// <summary>
    /// Tries to get the service of the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="serviceProvider">The service provider.</param>
    /// <param name="service">The output parameter to receive the service instance, or null if not found.</param>
    /// <returns>True if the service was found, false otherwise.</returns>
    public static bool TryGetService<T>(this IAIServiceProvider serviceProvider,
        [NotNullWhen(true)] out T? service) where T : IAIService
    {
        service = serviceProvider.GetService<T>();
        return service != null;
    }

    /// <summary>
    /// Tries to get the service of the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="serviceProvider">The service provider.</param>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="service">The output parameter to receive the service instance, or null if not found.</param>
    /// <returns>True if the service was found, false otherwise.</returns>
    public static bool TryGetService<T>(this IAIServiceProvider serviceProvider,
        string? name, [NotNullWhen(true)] out T? service) where T : IAIService
    {
        service = serviceProvider.GetService<T>(name);
        return service != null;
    }
}
