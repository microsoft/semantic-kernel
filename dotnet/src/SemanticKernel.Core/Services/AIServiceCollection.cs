// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// A collection of AI services that can be registered and built into an <see cref="IAIServiceProvider"/>.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
public class AIServiceCollection
{
    // A constant key for the default service
    private const string DefaultKey = "__DEFAULT__";

    // A dictionary that maps a service type to a nested dictionary of names and service instances or factories
    private readonly Dictionary<Type, Dictionary<string, Func<object>>> _services = new();

    // A dictionary that maps a service type to the name of the default service
    private readonly Dictionary<Type, string> _defaultIds = new();

    /// <summary>
    /// Registers a singleton service instance with the default name.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="service">The service instance.</param>
    /// <exception cref="ArgumentNullException">The service instance is null.</exception>
    public void SetService<T>(T service) where T : IAIService
        => this.SetService(DefaultKey, service, true);

    /// <summary>
    /// Registers a singleton service instance with an optional name and default flag.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="service">The service instance.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <exception cref="ArgumentNullException">The service instance is null.</exception>
    /// <exception cref="ArgumentException">The name is empty or whitespace.</exception>
    public void SetService<T>(string? name, T service, bool setAsDefault = false) where T : IAIService
        => this.SetService<T>(name, (() => service), setAsDefault);

    /// <summary>
    /// Registers a transient service factory with the default name.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    public void SetService<T>(Func<T> factory) where T : IAIService
        => this.SetService<T>(DefaultKey, factory, true);

    /// <summary>
    /// Registers a transient service factory with an optional name and default flag.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    /// <exception cref="ArgumentException">The name is empty or whitespace.</exception>
    public void SetService<T>(string? name, Func<T> factory, bool setAsDefault = false) where T : IAIService
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
        if (name == null || setAsDefault || !this.HasDefault<T>())
        {
            // Update the default name for the service type
            this._defaultIds[type] = name ?? DefaultKey;
        }

        var objectFactory = factory as Func<object>;

        // Register the factory with the given name
        namedServices[name ?? DefaultKey] = objectFactory
                                            ?? throw new InvalidOperationException("Service factory is an invalid format");
    }

    /// <summary>
    /// Builds an <see cref="IAIServiceProvider"/> from the registered services and default names.
    /// </summary>
    /// <returns>An <see cref="IAIServiceProvider"/> containing the registered services.</returns>
    public IAIServiceProvider Build()
    {
        // Create a clone of the services and defaults Dictionaries to prevent further changes
        // by the services provider.
        var servicesClone = this._services.ToDictionary(
            typeCollection => typeCollection.Key,
            typeCollection => typeCollection.Value.ToDictionary(
                service => service.Key,
                service => service.Value));

        var defaultsClone = this._defaultIds.ToDictionary(
            typeDefault => typeDefault.Key,
            typeDefault => typeDefault.Value);

        return new AIServiceProvider(servicesClone, defaultsClone);
    }

    private bool HasDefault<T>() where T : IAIService
        => this._defaultIds.TryGetValue(typeof(T), out var defaultName)
            && !string.IsNullOrEmpty(defaultName);
}
