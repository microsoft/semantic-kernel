// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Reflection;
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
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static IKernelPlugin CreateFromObject<T>(string? pluginName = null, ILoggerFactory? loggerFactory = null) where T : new() =>
        CreateFromObject(new T(), pluginName, loggerFactory);

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
    public static IKernelPlugin CreateFromObject(object target, string? pluginName = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(target);

        pluginName ??= target.GetType().Name;
        Verify.ValidPluginName(pluginName);

        MethodInfo[] methods = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);

        // Filter out non-SKFunctions and fail if two functions have the same name (with or without the same casing).
        KernelPlugin plugin = new(pluginName, target.GetType().GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description);
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<KernelFunctionAttribute>() is not null)
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
