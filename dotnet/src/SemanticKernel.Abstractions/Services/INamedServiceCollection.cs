// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Services;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix",
    Justification = "This is a collection, and is modeled after ServiceCollection")]
public interface INamedServiceCollection
{
    /// <summary>
    /// Registers a singleton service instance with the default name.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="service">The service instance.</param>
    /// <exception cref="ArgumentNullException">The service instance is null.</exception>
    void SetService<T>(T service);

    /// <summary>
    /// Registers a singleton service instance with an optional name and default flag.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="service">The service instance.</param>
    /// <param name="isDefault">Whether the service should be the default for its type.</param>
    /// <exception cref="ArgumentNullException">The service instance is null.</exception>
    /// <exception cref="ArgumentException">The name is empty or whitespace.</exception>
    void SetService<T>(string name, T service, bool isDefault = false);

    /// <summary>
    /// Registers a transient service factory with the default name.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    void SetServiceFactory<T>(Func<T> factory);

    /// <summary>
    /// Registers a transient service factory with an optional name and default flag.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <param name="isDefault">Whether the service should be the default for its type.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    /// <exception cref="ArgumentException">The name is empty or whitespace.</exception>
    void SetServiceFactory<T>(string name, Func<T> factory, bool isDefault = false);

    /// <summary>
    /// Registers a transient service factory that takes a service provider as a parameter, with the default name.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    void SetServiceFactory<T>(Func<INamedServiceProvider, T> factory);

    /// <summary>
    /// Registers a transient service factory that takes a service provider as a parameter, with an optional name and default flag.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service, or null for the default service.</param>
    /// <param name="factory">The factory function to create the service instance.</param>
    /// <param name="isDefault">Whether the service should be the default for its type.</param>
    /// <exception cref="ArgumentNullException">The factory function is null.</exception>
    /// <exception cref="ArgumentException">The name is empty or whitespace.</exception>
    void SetServiceFactory<T>(string name, Func<INamedServiceProvider, T> factory, bool isDefault = false);

    /// <summary>
    /// Tries to set the default service for the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service.</param>
    /// <returns>True if the service was found and set as the default, false otherwise.</returns>
    bool TrySetDefault<T>(string name);

    /// <summary>
    /// Tries to remove the service of the specified type and name, and returns a value indicating whether the operation succeeded.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    /// <param name="name">The name of the service.</param>
    /// <returns>True if the service was found and removed, false otherwise.</returns>
    bool TryRemove<T>(string name);

    /// <summary>
    /// Removes all the services of the specified type.
    /// </summary>
    /// <typeparam name="T">The type of the service.</typeparam>
    void Clear<T>();

    /// <summary>
    /// Removes all the services.
    /// </summary>
    void Clear();
}
