// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Provides named services of type <typeparamref name="TService"/>. Allows for the registration and retrieval of services by name.
/// </summary>
/// <typeparam name="TService">The type of service provided by this provider.</typeparam>
/// <example>
/// <code>
/// var services = new Dictionary&lt;Type, Dictionary&lt;string, Func&lt;object&gt;&gt;&gt;();
/// var defaultIds = new Dictionary&lt;Type, string&gt;();
/// var provider = new NamedServiceProvider&lt;IMyService&gt;(services, defaultIds);
/// </code>
/// </example>
public class NamedServiceProvider<TService> : INamedServiceProvider<TService>
{
    // A dictionary that maps a service type to a nested dictionary of names and service instances or factories
    private readonly Dictionary<Type, Dictionary<string, Func<object>>> _services;

    // A dictionary that maps a service type to the name of the default service
    private readonly Dictionary<Type, string> _defaultIds;

    /// <summary>
    /// Initializes a new instance of the <see cref="NamedServiceProvider{TService}"/> class.
    /// </summary>
    /// <param name="services">A dictionary that maps a service type to a nested dictionary of names and service instances or factories.</param>
    /// <param name="defaultIds">A dictionary that maps a service type to the name of the default service.</param>
    public NamedServiceProvider(
        Dictionary<Type, Dictionary<string, Func<object>>> services,
        Dictionary<Type, string> defaultIds)
    {
        this._services = services;
        this._defaultIds = defaultIds;
    }

    /// <inheritdoc/>
    public T? GetService<T>(string? name = null) where T : TService
    {
        // Return the service, casting or invoking the factory if needed
        var factory = this.GetServiceFactory<T>(name);
        if (factory is Func<T>)
        {
            return factory.Invoke();
        }

        return default;
    }

    /// <inheritdoc/>
    private string? GetDefaultServiceName<T>() where T : TService
    {
        // Returns the name of the default service for the given type, or null if none
        var type = typeof(T);
        if (this._defaultIds.TryGetValue(type, out var name))
        {
            return name;
        }

        return null;
    }

    private Func<T>? GetServiceFactory<T>(string? name = null) where T : TService
    {
        // Get the nested dictionary for the service type
        if (this._services.TryGetValue(typeof(T), out var namedServices))
        {
            Func<object>? serviceFactory = null;

            // If the name is not specified, try to load the default factory
            name ??= this.GetDefaultServiceName<T>();
            if (name != null)
            {
                // Check if there is a service registered with the given name
                namedServices.TryGetValue(name, out serviceFactory);
            }

            return serviceFactory as Func<T>;
        }

        return null;
    }
}
