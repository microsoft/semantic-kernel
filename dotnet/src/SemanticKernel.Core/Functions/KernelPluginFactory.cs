// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides static factory methods for creating commonly-used plugin implementations.
/// </summary>
public static class KernelPluginFactory
{
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="serviceProvider">
    /// The <see cref="IServiceProvider"/> to use for resolving any required services, such as an <see cref="ILoggerFactory"/>
    /// and any services required to satisfy a constructor on <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin CreateFromType<T>(string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        serviceProvider ??= EmptyServiceProvider.Instance;
        return CreateFromObject(ActivatorUtilities.CreateInstance<T>(serviceProvider)!, pluginName, serviceProvider?.GetService<ILoggerFactory>());
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin CreateFromObject(object target, string? pluginName = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(target);

        pluginName ??= target.GetType().Name;
        Verify.ValidPluginName(pluginName);

        MethodInfo[] methods = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);

        // Filter out non-SKFunctions and fail if two functions have the same name (with or without the same casing).
        var functions = new List<KernelFunction>();
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<KernelFunctionAttribute>() is not null)
            {
                functions.Add(KernelFunctionFactory.CreateFromMethod(method, target, loggerFactory: loggerFactory));
            }
        }
        if (functions.Count == 0)
        {
            throw new ArgumentException($"The {target.GetType()} instance doesn't expose any public [KernelFunction]-attributed methods.");
        }

        if (loggerFactory is not null)
        {
            ILogger logger = loggerFactory.CreateLogger(target.GetType());
            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Created plugin {PluginName} with {IncludedFunctions} [KernelFunction] methods out of {TotalMethods} methods found.", pluginName, functions.Count, methods.Length);
            }
        }

        var description = target.GetType().GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description;

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin CreateFromFunctions(string pluginName, IEnumerable<KernelFunction>? functions) =>
        CreateFromFunctions(pluginName, description: null, functions);

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin CreateFromFunctions(string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null) =>
        new DefaultKernelPlugin(pluginName, description, functions);
}
