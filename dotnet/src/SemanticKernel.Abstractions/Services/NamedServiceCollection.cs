// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Services;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix",
    Justification = "This is a collection, and is modeled after ServiceCollection")]
public class NamedServiceCollection : INamedServiceCollection, INamedServiceProvider
{
    // A constant key for the default service
    private const string DefaultKey = "__DEFAULT__";

    // A dictionary that maps a service type to a nested dictionary of names and service instances or factories
    private readonly Dictionary<Type, Dictionary<string, object>> _services = new();

    // A dictionary that maps a service type to the name of the default service
    private readonly Dictionary<Type, string> _defaultIds = new();

    #region INamedServiceCollection implementation

    /// <inheritdoc/>
    public void SetSingleton<T>(T service)
    {
        this.SetSingleton<T>(DefaultKey, service, true);
    }

    /// <inheritdoc/>
    public void SetSingleton<T>(string? name, T service, bool isDefault = false)
    {
        // Validate the service instance
        if (service == null)
        {
            throw new ArgumentNullException(nameof(service));
        }

        // Validate the name, if provided
        if (name != null && string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Provided name is empty or whitespace.", nameof(name));
        }

        // Get or create the nested dictionary for the service type
        var type = typeof(T);
        if (!this._services.TryGetValue(type, out var namedServices))
        {
            namedServices = new Dictionary<string, object>();
            this._services[type] = namedServices;
        }

        // Check if the name is null or the default flag is true
        if (name == null || isDefault)
        {
            // Update the default name for the service type
            this._defaultIds[type] = name ?? DefaultKey;
        }

        // Register the service with the given name
        namedServices[name ?? DefaultKey] = service;
    }

    /// <inheritdoc/>
    public void SetTransient<T>(Func<T> factory)
    {
        this.SetTransient<T>(DefaultKey, factory, true);
    }

    /// <inheritdoc/>
    // Registers a transient service factory with an optional name and default flag
    public void SetTransient<T>(string? name, Func<T> factory, bool isDefault = false)
    {
        // Validate the factory function
        if (factory == null)
        {
            throw new ArgumentNullException(nameof(factory));
        }

        // Validate the name, if provided
        if (name != null && string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Provided name is empty or whitespace.", nameof(name));
        }

        // Get or create the nested dictionary for the service type
        var type = typeof(T);
        if (!this._services.TryGetValue(type, out var namedServices))
        {
            namedServices = new Dictionary<string, object>();
            this._services[type] = namedServices;
        }

        // Check if the name is empty or the default flag is true
        if (name == null || isDefault)
        {
            // Update the default name for the service type
            this._defaultIds[type] = name ?? DefaultKey;
        }

        // Register the factory with the given name
        namedServices[name ?? DefaultKey] = factory;
    }

    /// <inheritdoc/>
    public void SetTransient<T>(Func<INamedServiceProvider, T> factory)
    {
        this.SetTransient<T>(DefaultKey, factory, true);
    }

    /// <inheritdoc/>
    public void SetTransient<T>(string? name, Func<INamedServiceProvider, T> factory, bool isDefault = false)
    {
        // Registers a transient service factory that takes a service provider as a parameter, with an optional name and default flag

        // Validate the factory function
        if (factory == null)
        {
            throw new ArgumentNullException(nameof(factory));
        }

        // Get or create the nested dictionary for the service type
        var type = typeof(T);
        if (!this._services.TryGetValue(type, out var namedServices))
        {
            namedServices = new Dictionary<string, object>();
            this._services[type] = namedServices;
        }

        // Check if the name is empty or the default flag is true
        if (name == null || isDefault)
        {
            // Register the factory as the default
            namedServices[DefaultKey] = factory;
            // Update the default name for the service type
            this._defaultIds[type] = name ?? DefaultKey;
        }

        // Register the factory with the given name
        namedServices[name ?? DefaultKey] = factory;
    }

    /// <inheritdoc/>
    public bool TryRemove<T>(string name)
    {
        var type = typeof(T);
        if (this._services.TryGetValue(type, out var namedServices)
            && namedServices.Remove(name))
        {
            // Check if the removed service was the default
            if (this._defaultIds.TryGetValue(type, out var defaultName)
                && defaultName == name)
            {
                // Remove the default name for the service type
                this._defaultIds.Remove(type);
            }
            return true;
        }

        return false;
    }

    /// <inheritdoc/>
    public void Clear<T>()
    {
        var type = typeof(T);
        this._services.Remove(type);
        this._defaultIds.Remove(type);
    }

    /// <inheritdoc/>
    public void Clear()
    {
        this._services.Clear();
        this._defaultIds.Clear();
    }

    #endregion INamedServiceCollection

    #region INamedServiceProvider implementation

    /// <inheritdoc/>
    public T? GetService<T>(string? name = null)
    {
        // Return the service, casting or invoking the factory if needed
        return this.GetServiceRegistration<T>(name) switch
        {
            null => default,
            Func<T> factory => factory(), // Invoke the factory with no argument
            Func<INamedServiceProvider, T> factory => factory(this), // Invoke the factory with the service provider
            T instance => instance, // Cast the service instance
            _ => throw new InvalidCastException(
                $"The service of name {name ?? "<NONE>"} is not compatible with {typeof(T)}.")
        };
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
    public T GetRequiredService<T>(string? name = null)
    {
        T? service = this.GetService<T>(name);
        return service ?? throw new InvalidOperationException(
            $"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
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

    private object? GetServiceRegistration<T>(string? name = null)
    {
        // Get the nested dictionary for the service type
        var type = typeof(T);
        object? service = null;
        if (this._services.TryGetValue(type, out var namedServices))
        {
            // If the name is not the default key, check if there is only one named service registered
            if (name == null && namedServices.Count == 1)
            {
                // Return the only named service, casting or invoking the factory if needed
                service = namedServices.Values.First();
            }
            else
            {
                // Check if there is a service registered with the given name
                // Use the default key if the name is not specified.
                namedServices.TryGetValue(name ?? DefaultKey, out service);
            }
        }

        return null;
    }

    #endregion INamedServiceProvider
}
