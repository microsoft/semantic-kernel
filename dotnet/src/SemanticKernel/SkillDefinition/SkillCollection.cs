// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Semantic Kernel default skill collection class.
/// The class holds a list of all the functions, native and semantic, known to the kernel instance.
/// The list is used by the planner and when executing pipelines of function compositions.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
[DebuggerTypeProxy(typeof(IReadOnlySkillCollectionTypeProxy))]
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public class SkillCollection : ISkillCollection
{
    internal const string GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /// <summary>
    /// Initializes a new instance of the <see cref="SkillCollection"/> class.
    /// </summary>
    /// <param name="loggerFactory">The logger factory.</param>
    public SkillCollection(ILoggerFactory? loggerFactory = null)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SkillCollection)) : NullLogger.Instance;

        // Important: names are case insensitive
        this._skillCollection = new(StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Adds a function to the skill collection.
    /// </summary>
    /// <param name="functionInstance">The function instance to add.</param>
    /// <returns>The updated skill collection.</returns>
    public ISkillCollection AddFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance);

        ConcurrentDictionary<string, ISKFunction> skill = this._skillCollection.GetOrAdd(functionInstance.SkillName, static _ => new(StringComparer.OrdinalIgnoreCase));
        skill[functionInstance.Name] = functionInstance;

        return this;
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName) =>
        this.GetFunction(GlobalSkill, functionName);

    /// <inheritdoc/>
    public ISKFunction GetFunction(string skillName, string functionName)
    {
        if (!this.TryGetFunction(skillName, functionName, out ISKFunction? functionInstance))
        {
            this.ThrowFunctionNotAvailable(skillName, functionName);
        }

        return functionInstance;
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction) =>
        this.TryGetFunction(GlobalSkill, functionName, out availableFunction);

    /// <inheritdoc/>
    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        Verify.NotNull(skillName);
        Verify.NotNull(functionName);

        if (this._skillCollection.TryGetValue(skillName, out ConcurrentDictionary<string, ISKFunction>? skill))
        {
            return skill.TryGetValue(functionName, out availableFunction);
        }

        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public IReadOnlyList<FunctionView> GetFunctionsView()
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
    private void ThrowFunctionNotAvailable(string skillName, string functionName)
    {
        this._logger.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new SKException($"Function not available {skillName}.{functionName}");
    }

    private readonly ILogger _logger;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _skillCollection;

    #endregion
}
