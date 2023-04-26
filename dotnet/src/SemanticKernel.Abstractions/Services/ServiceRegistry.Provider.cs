// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Services;

public partial class ServiceRegistry : INamedServiceProvider
{
    #region INamedServiceProvider implementation

    /// <inheritdoc/>
    public T? GetService<T>(string? name = null)
    {
        // Return the service, casting or invoking the factory if needed
        var factory = this.GetServiceFactory<T>(name);
        if (factory is Func<INamedServiceProvider, T>)
        {
            return factory.Invoke(this);
        }

        return default;
    }

    /// <inheritdoc/>
    public bool TryGetService<T>([NotNullWhen(true)] out T? service)
    {
        try
        {
            service = this.GetService<T>();
            return (service != null);
        }
        catch (InvalidCastException)
        {
        }

        service = default;
        return false;
    }

    /// <inheritdoc/>
    public bool TryGetService<T>(string name, [NotNullWhen(true)] out T? service)
    {
        try
        {
            service = this.GetService<T>(name);
            return (service != null);
        }
        catch (InvalidCastException)
        {
        }

        service = default;
        return false;
    }

    /// <inheritdoc/>
    public bool TrySetDefault<T>(string name)
    {
        if (this.TryGetService<T>(name, out var service))
        {
            this._defaultIds[typeof(T)] = name;
            return true;
        }

        return false;
    }

    /// <inheritdoc/>
    public IEnumerable<string> GetServiceNames<T>()
    {
        if (this._services.TryGetValue(typeof(T), out var dict))
        {
            return dict.Keys;
        }

        return Enumerable.Empty<string>();
    }

    /// <inheritdoc/>
    public string? GetDefaultServiceName<T>()
    {
        // Returns the name of the default service for the given type, or null if none
        var type = typeof(T);
        if (this._defaultIds.TryGetValue(type, out var name))
        {
            return name;
        }
        else if (this._services.TryGetValue(typeof(T), out var services))
        {
            if (services.Count == 1)
            {
                return services.Keys.First();
            }
        }

        return null;
    }

    /// <inheritdoc/>
    public bool HasServiceName<T>(string? name = null)
    {
        // If a name is specified, check if there is a service registered with the given name
        // If none is specified, check that there is a default service of this type.
        return (this.GetServiceFactory<T>(name) != null);

    }

    #endregion INamedServiceProvider

    private Func<INamedServiceProvider, T>? GetServiceFactory<T>(string? name = null)
    {
        // Get the nested dictionary for the service type
        if (this._services.TryGetValue(typeof(T), out var namedServices))
        {
            Func<INamedServiceProvider, object>? service = null;

            // If the name is not specified, try to load the default factory
            name ??= this.GetDefaultServiceName<T>();
            if (name != null)
            {
                // Check if there is a service registered with the given name
                namedServices.TryGetValue(name, out service);
            }

            var foo =  service as Func<INamedServiceProvider, T>;
            return foo;
        }

        return null;
    }
}

