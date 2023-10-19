// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Semantic Kernel default function collection class.
/// The class holds a list of all the functions, native and semantic, known to the kernel instance.
/// The list is used by the planner and when executing pipelines of function compositions.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
[DebuggerTypeProxy(typeof(IReadOnlyFunctionCollectionTypeProxy))]
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public class FunctionCollection : IFunctionCollection
{
    /// <summary>
    /// Plugin name used when storing global functions.
    /// </summary>
    public const string GlobalFunctionsPluginName = "_GLOBAL_FUNCTIONS_";

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    public FunctionCollection() : this((IReadOnlyFunctionCollection?)null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    /// <param name="readOnlyFunctionCollection">Collection of functions with which to populate this instance.</param>
    public FunctionCollection(IReadOnlyFunctionCollection? readOnlyFunctionCollection)
    {
        // Important: names are case insensitive
        this._functionCollection = new(StringComparer.OrdinalIgnoreCase);

        if (readOnlyFunctionCollection is not null)
        {
            foreach (var functionView in readOnlyFunctionCollection.GetFunctionViews())
            {
                this.AddFunction(readOnlyFunctionCollection.GetFunction(functionView.PluginName, functionView.Name));
            }
        }
    }

    /// <summary>
    /// Adds a function to the function collection.
    /// </summary>
    /// <param name="functionInstance">The function instance to add.</param>
    /// <returns>The updated function collection.</returns>
    public IFunctionCollection AddFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance);

        ConcurrentDictionary<string, ISKFunction> functions = this._functionCollection.GetOrAdd(functionInstance.PluginName, static _ => new(StringComparer.OrdinalIgnoreCase));
        functions[functionInstance.Name] = functionInstance;

        return this;
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName) =>
        this.GetFunction(GlobalFunctionsPluginName, functionName);

    /// <inheritdoc/>
    public ISKFunction GetFunction(string pluginName, string functionName)
    {
        pluginName = !string.IsNullOrWhiteSpace(pluginName) ? pluginName : GlobalFunctionsPluginName;

        if (!this.TryGetFunction(pluginName, functionName, out ISKFunction? functionInstance))
        {
            throw new SKException($"Function not available {pluginName}.{functionName}");
        }

        return functionInstance;
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction) =>
        this.TryGetFunction(GlobalFunctionsPluginName, functionName, out availableFunction);

    /// <inheritdoc/>
    public bool TryGetFunction(string pluginName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        Verify.NotNull(pluginName);
        Verify.NotNull(functionName);

        if (this._functionCollection.TryGetValue(pluginName, out ConcurrentDictionary<string, ISKFunction>? functions))
        {
            return functions.TryGetValue(functionName, out availableFunction);
        }

        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public IReadOnlyList<FunctionView> GetFunctionViews()
    {
        var result = new List<FunctionView>();

        foreach (var functions in this._functionCollection.Values)
        {
            foreach (ISKFunction f in functions.Values)
            {
                result.Add(f.Describe());
            }
        }

        return result;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay => $"Count = {this._functionCollection.Count}";

    #region Obsolete to be removed
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    /// <param name="readOnlyFunctionCollection">Optional skill collection to copy from</param>
    /// <param name="loggerFactory">The logger factory.</param>
    [Obsolete("Use a constructor that doesn't accept an ILoggerFactory. This constructor will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public FunctionCollection(IReadOnlyFunctionCollection? readOnlyFunctionCollection = null, ILoggerFactory? loggerFactory = null) : this(readOnlyFunctionCollection)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    /// <param name="loggerFactory">The logger factory.</param>
    [Obsolete("Use a constructor that doesn't accept an ILoggerFactory. This constructor will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public FunctionCollection(ILoggerFactory? loggerFactory = null) : this()
    {
    }
    #endregion

    #region private ================================================================================

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _functionCollection;

    #endregion
}
