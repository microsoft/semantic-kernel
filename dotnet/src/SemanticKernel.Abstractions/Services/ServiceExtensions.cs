// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Services;
internal static class ServiceExtensions
{
    /// <summary>
    /// Get the service matching the given id or the default if an id is not provided or not found.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="services">The service provider.</param>
    /// <param name="serviceId">Optional identifier of the desired service.</param>
    /// <returns>The service matching the given id, the default service, or null.</returns>
    public static T? GetNamedServiceOrDefault<T>(
        this INamedServiceProvider services,
        string? serviceId = null)
    {
        if ((serviceId != null)
            && services.TryGetService<T>(serviceId, out var namedService))
        {
            return namedService;
        }

        return services.GetService<T>();
    }

    public static ILogger<T>? GetLogger<T>(this INamedServiceProvider services)
    {
        return services.GetService<ILoggerFactory>()?.CreateLogger<T>();
    }

    public static IDelegatingHandlerFactory? GetHttpRetryHandler(this INamedServiceProvider services)
    {
        return services.GetService<IDelegatingHandlerFactory>();
    }
}
