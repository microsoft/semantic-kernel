// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.Logging;
using System.Reflection;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>
/// Static factory methods for creating <see cref="ISKPlugin"/> instances
/// that expose functions for public attributed methods on an object.
/// </summary>
public static class SKPluginFromObject
{
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin Create<T>(string? pluginName = null, ILoggerFactory? loggerFactory = null) where T : new() =>
        Create(new T(), pluginName, loggerFactory);

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// Attributed methods must all have different names. Overloads are not supported.
    /// </remarks>
    public static ISKPlugin Create(object target, string? pluginName = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(target);

        pluginName ??= target.GetType().Name;
        Verify.ValidPluginName(pluginName);

        MethodInfo[] methods = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);

        // Filter out non-SKFunctions and fail if two functions have the same name (with or without the same casing).
        SKPlugin plugin = new(pluginName, target.GetType().GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description);
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<SKFunctionAttribute>() is not null)
            {
                plugin.AddFunctionFromMethod(method, target, loggerFactory: loggerFactory);
            }
        }

        if (loggerFactory is not null)
        {
            ILogger logger = loggerFactory.CreateLogger(target.GetType());
            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Created plugin {PluginName} with {IncludedFunctions} out of {TotalMethods} methods found.", pluginName, plugin.FunctionCount, methods.Length);
            }
        }

        return plugin;
    }
}
