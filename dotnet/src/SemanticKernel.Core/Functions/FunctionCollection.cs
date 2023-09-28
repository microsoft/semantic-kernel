// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
    /// <param name="readOnlyFunctionCollection">Optional skill collection to copy from</param>
    /// <param name="loggerFactory">The logger factory.</param>
    public FunctionCollection(IReadOnlyFunctionCollection? readOnlyFunctionCollection = null, ILoggerFactory? loggerFactory = null)
    {
        this._logger = loggerFactory?.CreateLogger(typeof(FunctionCollection)) ?? NullLogger.Instance;

        // Important: names are case insensitive
        this._functionCollection = new(StringComparer.OrdinalIgnoreCase);

        if (readOnlyFunctionCollection is not null)
        {
            this.Populate(readOnlyFunctionCollection);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    /// <param name="loggerFactory">The logger factory.</param>
    public FunctionCollection(ILoggerFactory? loggerFactory = null) : this(null, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    public FunctionCollection() : this(null, null)
    {
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
        if (!this.TryGetFunction(pluginName, functionName, out ISKFunction? functionInstance))
        {
            this.ThrowFunctionNotAvailable(pluginName, functionName);
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

    #region private ================================================================================

    /// <summary>
    /// Populates the current functions collection from another.
    /// </summary>
    /// <param name="readOnlyCollection">The target read only functions collection</param>
    /// <returns>A new editable functions collection copy</returns>
    private void Populate(IReadOnlyFunctionCollection readOnlyCollection)
    {
        foreach (var functionView in readOnlyCollection.GetFunctionViews())
        {
            this.AddFunction(readOnlyCollection.GetFunction(functionView.PluginName, functionView.Name));
        }
    }

    [DoesNotReturn]
    private void ThrowFunctionNotAvailable(string pluginName, string functionName)
    {
        this._logger.LogError("Function not available: plugin:{PluginName} function:{FunctionName}", pluginName, functionName);
        throw new SKException($"Function not available {pluginName}.{functionName}");
    }

    private readonly ILogger _logger;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _functionCollection;

    #endregion
}
