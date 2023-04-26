// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;

namespace Microsoft.SemanticKernel.Services;
public partial class ServiceRegistry : INamedServiceCollection
{
    #region INamedServiceCollection implementation

    /// <inheritdoc/>
    public void SetService<T>(T service)
        => this.SetService<T>(DefaultKey, service, true);

    /// <inheritdoc/>
    public void SetService<T>(string? name, T service, bool isDefault = false)
        => this.SetServiceFactory<T>(name, ((INamedServiceProvider sp) => service), isDefault);

    /// <inheritdoc/>
    public void SetServiceFactory<T>(Func<T> factory)
        => this.SetServiceFactory<T>(DefaultKey, factory, true);

    /// <inheritdoc/>
    // Registers a transient service factory with an optional name and default flag
    public void SetServiceFactory<T>(string? name, Func<T> factory, bool isDefault = false)
        => this.SetServiceFactory<T>(name, ((INamedServiceProvider sp) => factory()), isDefault);

    /// <inheritdoc/>
    public void SetServiceFactory<T>(Func<INamedServiceProvider, T> factory)
        => this.SetServiceFactory<T>(DefaultKey, factory, true);

    /// <inheritdoc/>
    public void SetServiceFactory<T>(string? name, Func<INamedServiceProvider, T> factory, bool isDefault = false)
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
            namedServices = new();
            this._services[type] = namedServices;
        }

        // Set as the default if the name is empty, or the default flag is true,
        // or there is no default name for the service type.
        if (name == null || isDefault || !this.HasDefault<T>())
        {
            // Update the default name for the service type
            this._defaultIds[type] = name ?? DefaultKey;
        }

        var objectFactory = factory as Func<INamedServiceProvider, object>;

        // Register the factory with the given name
        namedServices[name ?? DefaultKey] = objectFactory
            ?? throw new InvalidOperationException("Service factory is an invalid format");
    }

    /// <inheritdoc/>
    public bool TryRemove<T>(string name)
    {
        var type = typeof(T);
        if (this._services.TryGetValue(type, out var namedServices)
            && namedServices.TryRemove(name, out _))
        {
            // Check if the removed service was the default
            if (this._defaultIds.TryGetValue(type, out var defaultName)
                && defaultName == name)
            {
                // Check for other services of this type
                var nextService = namedServices.Keys.FirstOrDefault();
                if (nextService != null)
                {
                    // Set the default to the first service in the dictionary
                    this._defaultIds[type] = nextService;
                }
                else
                {
                    // Remove the default name for the service type
                    this._defaultIds.TryRemove(type, out _);
                }
            }
            return true;
        }

        return false;
    }

    /// <inheritdoc/>
    public void Clear<T>()
    {
        var type = typeof(T);
        this._services.TryRemove(type, out _);
        this._defaultIds.TryRemove(type, out _);
    }

    /// <inheritdoc/>
    public void Clear()
    {
        this._services.Clear();
        this._defaultIds.Clear();
    }

    #endregion INamedServiceCollection

    private bool HasDefault<T>()
        => this._defaultIds.TryGetValue(typeof(T), out var defaultName)
            && !string.IsNullOrEmpty(defaultName);
}
