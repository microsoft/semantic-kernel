// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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

    /// <summary>
    /// Gets a logger for the specified type.
    /// </summary>
    /// <typeparam name="T">The type of the class for which to provide logging.</typeparam>
    /// <param name="services">The service provider.</param>
    /// <returns></returns>
    public static ILogger<T> GetLogger<T>(this INamedServiceProvider services)
    {
        if (services.TryGetService<ILoggerFactory>(out var factory))
        {
            return factory.CreateLogger<T>();
        }

        if (services.TryGetService<ILogger>(out var logger))
        {
            return (ILogger<T>)logger;
        }

        return NullLogger<T>.Instance;
    }

    public static IDelegatingHandlerFactory? GetHttpRetryHandler(this INamedServiceProvider services)
    {
        return services.GetService<IDelegatingHandlerFactory>();
    }
}
