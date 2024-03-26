// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for working with <see cref="KernelPlugin"/>s and collections of them.</summary>
public static class KernelPluginExtensions
{
    /// <summary>Gets whether the plugins collection contains a plugin with the specified name.</summary>
    /// <param name="plugins">The plugins collections.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <returns>true if the plugins contains a plugin with the specified name; otherwise, false.</returns>
    public static bool Contains(this IReadOnlyKernelPluginCollection plugins, string pluginName)
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
    public static KernelFunction GetFunction(this IReadOnlyKernelPluginCollection plugins, string? pluginName, string functionName)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(functionName);

        if (!TryGetFunction(plugins, pluginName, functionName, out KernelFunction? function))
        {
            throw new KeyNotFoundException($"The plugin collection does not contain a plugin and/or function with the specified names. Plugin name - '{pluginName}', function name - '{functionName}'.");
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
    public static bool TryGetFunction(this IReadOnlyKernelPluginCollection plugins, string? pluginName, string functionName, [NotNullWhen(true)] out KernelFunction? func)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(functionName);

        if (string.IsNullOrWhiteSpace(pluginName))
        {
            foreach (KernelPlugin p in plugins)
            {
                if (p.TryGetFunction(functionName, out func))
                {
                    return true;
                }
            }
        }
        else
        {
            if (plugins.TryGetPlugin(pluginName!, out KernelPlugin? plugin) &&
                plugin.TryGetFunction(functionName, out func))
            {
                return true;
            }
        }

        func = null;
        return false;
    }

    /// <summary>Gets a collection of <see cref="KernelFunctionMetadata"/> instances, one for every function in every plugin in the plugins collection.</summary>
    /// <param name="plugins">The plugins collection.</param>
    /// <returns>A list of metadata over every function in the plugins collection</returns>
    public static IList<KernelFunctionMetadata> GetFunctionsMetadata(this IEnumerable<KernelPlugin> plugins)
    {
        Verify.NotNull(plugins);

        List<KernelFunctionMetadata> metadata = new();
        foreach (KernelPlugin plugin in plugins)
        {
            metadata.AddRange(plugin.GetFunctionsMetadata());
        }

        return metadata;
    }

    /// <summary>
    /// Given an <see cref="FunctionCallContent"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/> and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionCallContent">The <see cref="FunctionCallContent"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(this IReadOnlyKernelPluginCollection plugins, FunctionCallContent functionCallContent, [NotNullWhen(true)] out KernelFunction? function, out KernelArguments? arguments)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(functionCallContent);

        if (plugins.TryGetFunction(functionCallContent.PluginName, functionCallContent.FunctionName, out function))
        {
            // Add parameters to arguments
            arguments = null;
            if (functionCallContent.Arguments is not null)
            {
                if (JsonSerializer.Deserialize<IDictionary<string, object?>>(functionCallContent.Arguments) is { } args)
                {
                    arguments = new KernelArguments();
                    foreach (var argument in args)
                    {
                        arguments[argument.Key] = argument.Value?.ToString();
                    }
                }
            }

            return true;
        }

        // Function not found in collection
        arguments = null;
        return false;
    }
}
