// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides static factory methods for creating commonly-used plugin implementations.
/// </summary>
public static partial class KernelPluginFactory
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
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateFromType<T>(string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        serviceProvider ??= EmptyServiceProvider.Instance;
        return CreateFromObject(ActivatorUtilities.CreateInstance<T>(serviceProvider)!, pluginName, serviceProvider?.GetService<ILoggerFactory>());
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="serviceProvider">
    /// The <see cref="IServiceProvider"/> to use for resolving any required services, such as an <see cref="ILoggerFactory"/>
    /// and any services required to satisfy a constructor on <typeparamref name="T"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin CreateFromType<[DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(JsonSerializerOptions jsonSerializerOptions, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        serviceProvider ??= EmptyServiceProvider.Instance;
        return CreateFromObject<T>(ActivatorUtilities.CreateInstance<T>(serviceProvider)!, jsonSerializerOptions, pluginName, serviceProvider?.GetService<ILoggerFactory>());
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <paramref name="instanceType"/>.</summary>
    /// <param name="instanceType">
    /// Specifies the type of the object to wrap.
    /// </param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the <paramref name="instanceType"/>.
    /// </param>
    /// <param name="serviceProvider">
    /// The <see cref="IServiceProvider"/> to use for resolving any required services, such as an <see cref="ILoggerFactory"/>
    /// and any services required to satisfy a constructor on <paramref name="instanceType"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="instanceType"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateFromType(Type instanceType, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        serviceProvider ??= EmptyServiceProvider.Instance;
        return CreateFromObject(ActivatorUtilities.CreateInstance(serviceProvider, instanceType)!, pluginName, serviceProvider?.GetService<ILoggerFactory>());
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <paramref name="instanceType"/>.</summary>
    /// <param name="instanceType">
    /// Specifies the type of the object to wrap.
    /// </param>
    /// <param name="jsonSerializerOptions">
    /// The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.
    /// </param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the <paramref name="instanceType"/>.
    /// </param>
    /// <param name="serviceProvider">
    /// The <see cref="IServiceProvider"/> to use for resolving any required services, such as an <see cref="ILoggerFactory"/>
    /// and any services required to satisfy a constructor on <paramref name="instanceType"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="instanceType"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin CreateFromType([DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] Type instanceType, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        serviceProvider ??= EmptyServiceProvider.Instance;
        return CreateFromObject(ActivatorUtilities.CreateInstance(serviceProvider, instanceType)!, jsonSerializerOptions, pluginName, serviceProvider?.GetService<ILoggerFactory>());
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateFromObject(object target, string? pluginName = null, ILoggerFactory? loggerFactory = null)
    {
        return CreateFromObjectInternal(target, pluginName, loggerFactory: loggerFactory);
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    public static KernelPlugin CreateFromObject<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(T target, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(jsonSerializerOptions);
        return CreateFromObjectInternal(target, pluginName, jsonSerializerOptions, loggerFactory: loggerFactory);
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
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
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin CreateFromFunctions(string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null) =>
        new DefaultKernelPlugin(pluginName, description, functions);

    /// <summary>Creates a name for a plugin based on its type name.</summary>
    private static string CreatePluginName(Type type)
    {
        string name = type.Name;
        if (type.IsGenericType)
        {
            // Simple representation of generic arguments, without recurring into their generics
            var builder = new StringBuilder();
            AppendWithoutArity(builder, name);

            Type[] genericArgs = type.GetGenericArguments();
            for (int i = 0; i < genericArgs.Length; i++)
            {
                builder.Append('_');
                AppendWithoutArity(builder, genericArgs[i].Name);
            }

            name = builder.ToString();

            static void AppendWithoutArity(StringBuilder builder, string name)
            {
                int tickPos = name.IndexOf('`');
                if (tickPos >= 0)
                {
                    builder.Append(name, 0, tickPos);
                }
                else
                {
                    builder.Append(name);
                }
            }
        }

        // Replace invalid characters
        name = InvalidPluginNameCharactersRegex().Replace(name, "_");

        return name;
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private static KernelPlugin CreateFromObjectInternal<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(T target, string? pluginName = null, JsonSerializerOptions? jsonSerializerOptions = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(target);

        pluginName ??= CreatePluginName(target.GetType());
        KernelVerify.ValidPluginName(pluginName);

        MethodInfo[] methods = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static);

        // Filter out non-KernelFunctions and fail if two functions have the same name (with or without the same casing).
        var functions = new List<KernelFunction>();
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<KernelFunctionAttribute>() is not null)
            {
                if (jsonSerializerOptions is not null)
                {
                    functions.Add(KernelFunctionFactory.CreateFromMethod(method, jsonSerializerOptions, target, loggerFactory: loggerFactory));
                }
                else
                {
                    functions.Add(KernelFunctionFactory.CreateFromMethod(method, target, loggerFactory: loggerFactory));
                }
            }
        }
        if (functions.Count == 0)
        {
            throw new ArgumentException($"The {target.GetType()} instance doesn't implement any [KernelFunction]-attributed methods.");
        }

        if (loggerFactory?.CreateLogger(target.GetType()) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created plugin {PluginName} with {IncludedFunctions} [KernelFunction] methods out of {TotalMethods} methods found.", pluginName, functions.Count, methods.Length);
        }

        var description = target.GetType().GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description;

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }

#if NET
    [GeneratedRegex("[^0-9A-Za-z_]")]
    private static partial Regex InvalidPluginNameCharactersRegex();
#else
    private static Regex InvalidPluginNameCharactersRegex() => s_invalidPluginNameCharactersRegex;
    private static readonly Regex s_invalidPluginNameCharactersRegex = new("[^0-9A-Za-z_]", RegexOptions.Compiled);
#endif
}
