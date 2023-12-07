// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable CA1716 // Identifiers should not match keywords

namespace Microsoft.SemanticKernel;

/// <summary>Represents a plugin that may be registered with a <see cref="Kernel"/>.</summary>
/// <remarks>
/// A plugin is named read-only collection of functions. There is a many-to-many relationship between
/// plugins and functions: a plugin may contain any number of functions, and a function may
/// exist in any number of plugins.
/// </remarks>
public abstract class KernelPluginBase : IEnumerable<KernelFunction>
{
    /// <summary>Gets the name of the plugin.</summary>
    public string Name { get; }

    /// <summary>Gets a description of the plugin.</summary>
    public string Description { get; }

    /// <summary>Gets the function in the plugin with the specified name.</summary>
    /// <param name="functionName">The name of the function.</param>
    /// <returns>The function.</returns>
    /// <exception cref="KeyNotFoundException">The plugin does not contain a function with the specified name.</exception>
    public abstract KernelFunction this[string functionName] { get; }

    /// <summary>Initializes the new plugin from the provided name.</summary>
    /// <param name="name">The name for the plugin.</param>
    protected KernelPluginBase(string name) : this(name, description: null)
    {
    }

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="name">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="name"/> if plugin name is invalid.</exception>
    /// <exception cref="ArgumentException"><paramref name="name"/> if plugin with this name is already registered.</exception>
    protected KernelPluginBase(string name, string? description)
    {
        Verify.ValidPluginName(name);

        this.Name = name;
        this.Description = !string.IsNullOrWhiteSpace(description) ? description! : "";
    }

    /// <summary>Finds a function in the plugin by name.</summary>
    /// <param name="name">The name of the function to find.</param>
    /// <param name="function">If the plugin contains the requested function, the found function instance; otherwise, null.</param>
    /// <returns>true if the function was found in the plugin; otherwise, false.</returns>
    public abstract bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function);

    /// <inheritdoc/>
    public abstract IEnumerator<KernelFunction> GetEnumerator();

    /// <inheritdoc/>
    IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();
}
