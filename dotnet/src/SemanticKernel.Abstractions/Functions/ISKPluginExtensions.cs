// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for working with <see cref="ISKPlugin"/>s and collections of them.</summary>
public static class ISKPluginExtensions
{
    /// <summary>Gets whether the plugin contains a function with the specified name.</summary>
    /// <param name="plugin">The plugin.</param>
    /// <param name="functionName">The name of the function.</param>
    /// <returns>true if the plugin contains the specified function; otherwise, false.</returns>
    public static bool Contains(this ISKPlugin plugin, string functionName)
    {
        Verify.NotNull(plugin);
        Verify.NotNull(functionName);

        return plugin.TryGetFunction(functionName, out _);
    }

    /// <summary>Gets whether the plugin contains a function.</summary>
    /// <param name="plugin">The plugin.</param>
    /// <param name="function">The function.</param>
    /// <returns>true if the plugin contains the specified function; otherwise, false.</returns>
    public static bool Contains(this ISKPlugin plugin, KernelFunction function)
    {
        Verify.NotNull(plugin);
        Verify.NotNull(function);

        return plugin.TryGetFunction(function.Name, out KernelFunction? found) && found == function;
    }

    /// <summary>Gets whether the plugins collection contains a plugin with the specified name.</summary>
    /// <param name="plugins">The plugins collections.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <returns>true if the plugins contains a plugin with the specified name; otherwise, false.</returns>
    public static bool Contains(this IReadOnlySKPluginCollection plugins, string pluginName)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(pluginName);

        return plugins.TryGetPlugin(pluginName, out _);
    }

    /// <summary>Gets a function from the collection by plugin and function names.</summary>
    /// <param name="plugins">The collection.</param>
    /// <param name="pluginName">The name of the plugin storing the function.</param>
    /// <param name="functionName">The name of the function.</param>
    /// <returns>The function from the collection.</returns>
    public static KernelFunction GetFunction(this IReadOnlySKPluginCollection plugins, string? pluginName, string functionName)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(functionName);

        if (!TryGetFunction(plugins, pluginName, functionName, out KernelFunction? function))
        {
            throw new KeyNotFoundException("The plugin collection does not contain a plugin and/or function with the specified names.");
        }

        return function;
    }

    /// <summary>Gets a function from the collection by plugin and function names.</summary>
    /// <param name="plugins">The collection.</param>
    /// <param name="pluginName">The name of the plugin storing the function.</param>
    /// <param name="functionName">The name of the function.</param>
    /// <param name="func">The function, if found.</param>
    /// <returns>true if the specified plugin was found and the specified function was found in that plugin; otherwise, false.</returns>
    /// <remarks>
    /// If <paramref name="pluginName"/> is null or entirely whitespace, all plugins are searched for a function with the specified name,
    /// and the first one found is returned.
    /// </remarks>
    public static bool TryGetFunction(this IReadOnlySKPluginCollection plugins, string? pluginName, string functionName, [NotNullWhen(true)] out KernelFunction? func)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(functionName);

        if (string.IsNullOrWhiteSpace(pluginName))
        {
            foreach (ISKPlugin p in plugins)
            {
                if (p.TryGetFunction(functionName, out func))
                {
                    return true;
                }
            }
        }
        else
        {
            if (plugins.TryGetPlugin(pluginName!, out ISKPlugin? plugin) &&
                plugin.TryGetFunction(functionName, out func))
            {
                return true;
            }
        }

        func = null;
        return false;
    }

    /// <summary>Adds a collection of plugins to this plugin collection.</summary>
    /// <param name="destination">The collection to which <paramref name="plugins"/> should be added.</param>
    /// <param name="plugins">The plugins to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="plugins"/> is null.</exception>
    /// <exception cref="ArgumentNullException">A plugin in <paramref name="plugins"/> has a null <see cref="ISKPlugin.Name"/>.</exception>
    /// <exception cref="ArgumentException">A plugin with the same name as a plugin in <paramref name="plugins"/> already exists in the collection.</exception>
    public static void AddRange(this ISKPluginCollection destination, IEnumerable<ISKPlugin> plugins)
    {
        Verify.NotNull(destination);
        Verify.NotNull(plugins);

        foreach (ISKPlugin plugin in plugins)
        {
            destination.Add(plugin);
        }
    }

    /// <summary>Gets a collection of <see cref="SKFunctionMetadata"/> instances, one for every function in every plugin in the plugins collection.</summary>
    /// <param name="plugins">The plugins collection.</param>
    /// <returns>A list of views over every function in the plugins collection</returns>
    public static IList<SKFunctionMetadata> GetFunctionsMetadata(this IEnumerable<ISKPlugin> plugins)
    {
        Verify.NotNull(plugins);

        List<SKFunctionMetadata> views = new();
        foreach (ISKPlugin plugin in plugins)
        {
            foreach (KernelFunction function in plugin)
            {
                views.Add(new SKFunctionMetadata(function.GetMetadata()) { PluginName = plugin.Name });
            }
        }

        return views;
    }
}
