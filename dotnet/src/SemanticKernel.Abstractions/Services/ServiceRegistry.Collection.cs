// Copyright (c) Microsoft. All rights reserved.

using System;

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

        // Check if the name is empty or the default flag is true
        if (name == null || isDefault)
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
}
