// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
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
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public class SkillCollection : ISkillCollection
{
    internal const string GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /// <inheritdoc/>
    public IReadOnlySkillCollection ReadOnlySkillCollection { get; private set; }

    public SkillCollection(ILogger? log = null)
    {
        this._log = log ?? NullLogger.Instance;

        this.ReadOnlySkillCollection = new ReadOnlySkillCollection(this);

        // Important: names are case insensitive
        this._skillCollection = new(StringComparer.OrdinalIgnoreCase);
    }

    /// <inheritdoc/>
    public ISkillCollection AddSemanticFunction(ISKFunction functionInstance) =>
        this.AddFunction(functionInstance);

    /// <inheritdoc/>
    public ISkillCollection AddNativeFunction(ISKFunction functionInstance) =>
        this.AddFunction(functionInstance);

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
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this.TryGetFunction(GlobalSkill, functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        Verify.NotNull(skillName, nameof(skillName));
        Verify.NotNull(functionName, nameof(functionName));

        if (this._skillCollection.TryGetValue(skillName, out ConcurrentDictionary<string, ISKFunction>? skill))
        {
            return skill.TryGetValue(functionName, out functionInstance);
        }

        functionInstance = null;
        return false;
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string functionName) =>
        this.GetSemanticFunction(GlobalSkill, functionName);

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string skillName, string functionName)
    {
        if (!this.TryGetSemanticFunction(skillName, functionName, out ISKFunction? functionInstance))
        {
            this.ThrowFunctionNotAvailable(skillName, functionName);
        }

        return functionInstance;
    }

    /// <inheritdoc/>
    public bool TryGetSemanticFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this.TryGetSemanticFunction(GlobalSkill, functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetSemanticFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        if (this.TryGetFunction(skillName, functionName, out ISKFunction? func) && func.IsSemantic)
        {
            functionInstance = func;
            return true;
        }

        functionInstance = null;
        return false;
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string functionName) =>
        this.GetNativeFunction(GlobalSkill, functionName);

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string skillName, string functionName)
    {
        if (!this.TryGetNativeFunction(skillName, functionName, out ISKFunction? functionInstance))
        {
            this.ThrowFunctionNotAvailable(skillName, functionName);
        }

        return functionInstance;
    }

    /// <inheritdoc/>
    public bool TryGetNativeFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this.TryGetNativeFunction(GlobalSkill, functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetNativeFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        if (this.TryGetFunction(skillName, functionName, out ISKFunction? func) && !func.IsSemantic)
        {
            functionInstance = func;
            return true;
        }

        functionInstance = null;
        return false;
    }

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
    {
        var result = new FunctionsView();

        if (includeSemantic || includeNative)
        {
            foreach (var skill in this._skillCollection)
            {
                foreach (KeyValuePair<string, ISKFunction> f in skill.Value)
                {
                    if (f.Value.IsSemantic ? includeSemantic : includeNative)
                    {
                        result.AddFunction(f.Value.Describe());
                    }
                }
            }
        }

        return result;
    }

    #region private ================================================================================

    private SkillCollection AddFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance, "The function is NULL");

        ConcurrentDictionary<string, ISKFunction> skill = this._skillCollection.GetOrAdd(functionInstance.SkillName, static _ => new(StringComparer.OrdinalIgnoreCase));
        skill.TryAdd(functionInstance.Name, functionInstance);

        return this;
    }

    [DoesNotReturn]
    private void ThrowFunctionNotAvailable(string skillName, string functionName)
    {
        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    private readonly ILogger _log;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _skillCollection;

    #endregion
}
