// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Services;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix",
    Justification = "This is a collection, and is modeled after ServiceCollection")]
public class NamedServiceCollection : INamedServiceCollection
{
    // A constant key for the default service
    private const string DefaultKey = "__DEFAULT__";

    // A dictionary that maps a service type to a nested dictionary of names and service instances or factories
    private readonly Dictionary<Type, Dictionary<string, object>> _services;

    public NamedServiceCollection()
    {
        this._services = new Dictionary<Type, Dictionary<string, object>>();
    }

    public void AddSingleton<T>(T service)
    {
        this.AddSingleton<T>(DefaultKey, service, true);
    }

    // Registers a singleton service instance with an optional name and default flag
    public void AddSingleton<T>(string? name, T service, bool isDefault = false)
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
            // Register the service as the default
            namedServices[DefaultKey] = service;
        }

        // Check if the name is not empty
        if (name != null)
        {
            // Register the service with the given name
            namedServices[name!] = service;
        }
    }

    public void AddTransient<T>(Func<T> factory)
    {
        this.AddTransient<T>(DefaultKey, factory, true);
    }

    // Registers a transient service factory with an optional name and default flag
    public void AddTransient<T>(string? name, Func<T> factory, bool isDefault = false)
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
            // Register the factory as the default
            namedServices[DefaultKey] = factory;
        }

        // Check if the name is not empty
        if (name != null)
        {
            // Register the factory with the given name
            namedServices[name!] = factory;
        }
    }

    public void AddTransient<T>(Func<INamedServiceProvider, T> factory)
    {
        this.AddTransient<T>(DefaultKey, factory, true);
    }

    // Registers a transient service factory that takes a service provider as a parameter, with an optional name and default flag
    public void AddTransient<T>(string? name, Func<INamedServiceProvider, T> factory, bool isDefault = false)
    {
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
        }

        // Check if the name is not empty
        if (name != null)
        {
            // Register the factory with the given name
            namedServices[name!] = factory;
        }
    }

    public bool TryRemove<T>(string name)
    {
        return this._services.TryGetValue(typeof(T), out var namedServices)
            && namedServices.Remove(name);
    }

    public void Clear<T>()
    {
        this._services.Remove(typeof(T));
    }

    public void Clear()
    {
        this._services.Clear();
    }

    // Builds an immutable named service provider that can resolve the registered services
    //public INamedServiceProvider Build()
    //{
    //    // Create a shallow copy of the services dictionary and its nested dictionaries
    //    var servicesCopy = this._services.ToDictionary(
    //        kvp => kvp.Key, // Use the same service type as the key
    //        kvp => kvp.Value.ToDictionary( // Create a copy of the nested dictionary
    //            subKvp => subKvp.Key, // Use the same service name as the key
    //            subKvp => subKvp.Value // Use the same service instance or factory as the value
    //        )
    //    );

    //    return new NamedServiceProvider(servicesCopy);
    //}

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

    public T GetRequiredService<T>(string? name = null)
    {
        T? service = this.GetService<T>(name);
        return service ?? throw new InvalidOperationException(
            $"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
    }

    public bool TrySetDefault<T>(string name)
    {
        if (this._services.TryGetValue(typeof(T), out var namedServices)
            && namedServices.TryGetValue(name, out var service))
        {
            namedServices[DefaultKey] = service;
            return true;
        }

        return false;
    }

    public IEnumerable<string> GetServiceNames<T>()
    {
        if (this._services.TryGetValue(typeof(T), out var dict))
        {
            return dict.Keys.Where(s => s != DefaultKey);
        }

        return Enumerable.Empty<string>();
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
}
