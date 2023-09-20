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
/// Semantic Kernel default skill collection class.
/// The class holds a list of all the functions, native and semantic, known to the kernel instance.
/// The list is used by the planner and when executing pipelines of function compositions.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
[DebuggerTypeProxy(typeof(IReadOnlyFunctionCollectionTypeProxy))]
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public class FunctionCollection : IFunctionCollection
{
    internal const string GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCollection"/> class.
    /// </summary>
    /// <param name="loggerFactory">The logger factory.</param>
    public FunctionCollection(ILoggerFactory? loggerFactory = null)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(FunctionCollection)) : NullLogger.Instance;

        // Important: names are case insensitive
        this._skillCollection = new(StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Adds a function to the skill collection.
    /// </summary>
    /// <param name="functionInstance">The function instance to add.</param>
    /// <returns>The updated skill collection.</returns>
    public IFunctionCollection AddFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance);

        ConcurrentDictionary<string, ISKFunction> skill = this._skillCollection.GetOrAdd(functionInstance.PluginName, static _ => new(StringComparer.OrdinalIgnoreCase));
        skill[functionInstance.Name] = functionInstance;

        return this;
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName) =>
        this.GetFunction(GlobalSkill, functionName);

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
        this.TryGetFunction(GlobalSkill, functionName, out availableFunction);

    /// <inheritdoc/>
    public bool TryGetFunction(string pluginName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        Verify.NotNull(pluginName);
        Verify.NotNull(functionName);

        if (this._skillCollection.TryGetValue(pluginName, out ConcurrentDictionary<string, ISKFunction>? skill))
        {
            return skill.TryGetValue(functionName, out availableFunction);
        }

        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public IReadOnlyList<FunctionView> GetFunctionViews()
    {
        var result = new List<FunctionView>();

        foreach (var skill in this._skillCollection.Values)
        {
            foreach (ISKFunction f in skill.Values)
            {
                result.Add(f.Describe());
            }
        }

        return result;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    internal string DebuggerDisplay => $"Count = {this._skillCollection.Count}";

    #region private ================================================================================

    [DoesNotReturn]
    private void ThrowFunctionNotAvailable(string pluginName, string functionName)
    {
        this._logger.LogError("Function not available: skill:{0} function:{1}", pluginName, functionName);
        throw new SKException($"Function not available {pluginName}.{functionName}");
    }

    private readonly ILogger _logger;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _skillCollection;

    #endregion
}
