// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.Logging;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an <see cref="ISKPlugin"/> implementation around a collection of functions
/// as well as static factory methods for creating commonly-used plugin implementations.
/// </summary>
[DebuggerDisplay("Name = {Name}, Functions = {FunctionCount}")]
[DebuggerTypeProxy(typeof(SKPlugin.TypeProxy))]
public sealed class SKPlugin : ISKPlugin
{
    /// <summary>The collection of functions associated with this plugin.</summary>
    private readonly Dictionary<string, ISKFunction> _functions;

    /// <summary>Initializes the new plugin from the provided name.</summary>
    /// <param name="name">The name for the plugin.</param>
    public SKPlugin(string name) : this(name, description: null, functions: null)
    {
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="name">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    public SKPlugin(string name, IEnumerable<ISKFunction>? functions) : this(name, description: null, functions)
    {
    }

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="name">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public SKPlugin(string name, string? description, IEnumerable<ISKFunction>? functions = null)
    {
        Verify.ValidPluginName(name);

        this.Name = name;
        this.Description = !string.IsNullOrWhiteSpace(description) ? description! : "";

        this._functions = new Dictionary<string, ISKFunction>(StringComparer.OrdinalIgnoreCase);
        if (functions is not null)
        {
            foreach (ISKFunction f in functions)
            {
                Verify.NotNull(f, nameof(functions));
                this._functions.Add(f.Name, f);
            }
        }
    }

    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <summary>Gets the number of functions in this plugin.</summary>
    public int FunctionCount => this._functions.Count;

    /// <inheritdoc/>
    public ISKFunction this[string functionName] => this._functions[functionName];

    /// <inheritdoc/>
    public bool TryGetFunction(string name, [NotNullWhen(true)] out ISKFunction? function) =>
        this._functions.TryGetValue(name, out function);

    /// <summary>Adds a function to the plugin.</summary>
    /// <param name="function">The function to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="function"/>'s <see cref="ISKFunction.Name"/> is null.</exception>
    /// <exception cref="ArgumentException">A function with the same <see cref="ISKFunction.Name"/> already exists in this plugin.</exception>
    public void AddFunction(ISKFunction function)
    {
        Verify.NotNull(function);
        this._functions.Add(function.Name, function);
    }

    /// <summary>Adds all of the functions in the specified <paramref name="functions"/> collection to this plugin.</summary>
    /// <param name="functions">The functions to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> is null.</exception>
    /// <exception cref="ArgumentNullException">A function in <paramref name="functions"/>'s has a null <see cref="ISKFunction.Name"/>.</exception>
    /// <exception cref="ArgumentException">A function with the same <see cref="ISKFunction.Name"/> already exists in this plugin.</exception>
    public void AddFunctions(IEnumerable<ISKFunction> functions)
    {
        Verify.NotNull(functions);

        foreach (ISKFunction function in functions)
        {
            this.AddFunction(function);
        }
    }

    /// <inheritdoc/>
    public IEnumerator<ISKFunction> GetEnumerator() => this._functions.Values.GetEnumerator();

    /// <inheritdoc/>
    IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();

    /// <summary>Debugger type proxy for the plugin.</summary>
    private sealed class TypeProxy
    {
        private readonly SKPlugin _plugin;

        public TypeProxy(SKPlugin plugin) => this._plugin = plugin;

        public string Name => this._plugin.Name;

        public string Description => this._plugin.Description;

        public ISKFunction[] Functions => this._plugin._functions.Values.OrderBy(f => f.Name, StringComparer.OrdinalIgnoreCase).ToArray();
    }

    #region Factory Methods
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin FromObject<T>(string? pluginName = null, ILoggerFactory? loggerFactory = null) where T : new() =>
        FromObject(new T(), pluginName, loggerFactory);

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// Attributed methods must all have different names. Overloads are not supported.
    /// </remarks>
    public static ISKPlugin FromObject(object target, string? pluginName = null, ILoggerFactory? loggerFactory = null)
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
    #endregion
}
