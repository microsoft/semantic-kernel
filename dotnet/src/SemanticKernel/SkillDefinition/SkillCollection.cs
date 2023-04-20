// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Semantic Kernel default skill collection class.
/// The class holds a list of all the functions, native and semantic, known to the kernel instance.
/// The list is used by the planner and when executing pipelines of function compositions.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1710:Identifiers should have correct suffix", Justification = "It is a collection")]
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public class SkillCollection : ISkillCollection
{
    internal const string GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /// <inheritdoc/>
    public IReadOnlySkillCollection ReadOnlySkillCollection { get; private set; }

    public SkillCollection(ILogger? log = null)
    {
        if (log != null) { this._log = log; }

        this.ReadOnlySkillCollection = new ReadOnlySkillCollection(this);

        // Important: names are case insensitive
        this._skillCollection = new(StringComparer.OrdinalIgnoreCase);
    }

    /// <inheritdoc/>
    public ISkillCollection AddSemanticFunction(ISKFunction functionInstance)
    {
        if (!this._skillCollection.ContainsKey(functionInstance.SkillName))
        {
            // Important: names are case insensitive
            this._skillCollection[functionInstance.SkillName] = new(StringComparer.OrdinalIgnoreCase);
        }

        this._skillCollection[functionInstance.SkillName][functionInstance.Name] = functionInstance;

        return this;
    }

    /// <inheritdoc/>
    public ISkillCollection AddNativeFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance, "The function is NULL");
        if (!this._skillCollection.ContainsKey(functionInstance.SkillName))
        {
            // Important: names are case insensitive
            this._skillCollection[functionInstance.SkillName] = new(StringComparer.OrdinalIgnoreCase);
        }

        this._skillCollection[functionInstance.SkillName][functionInstance.Name] = functionInstance;
        return this;
    }

    /// <inheritdoc/>
    public bool HasFunction(string skillName, string functionName)
    {
        return this._skillCollection.ContainsKey(skillName) &&
               this._skillCollection[skillName].ContainsKey(functionName);
    }

    /// <inheritdoc/>
    public bool HasFunction(string functionName)
    {
        return this._skillCollection.ContainsKey(GlobalSkill) &&
               this._skillCollection[GlobalSkill].ContainsKey(functionName);
    }

    /// <inheritdoc/>
    public bool HasSemanticFunction(string skillName, string functionName)
    {
        return this.HasFunction(skillName, functionName)
               && this._skillCollection[skillName][functionName].IsSemantic;
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string skillName, string functionName)
    {
        return this.HasFunction(skillName, functionName)
               && !this._skillCollection[skillName][functionName].IsSemantic;
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string functionName)
    {
        return this.HasNativeFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName)
    {
        return this.GetFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string skillName, string functionName)
    {
        if (this.HasFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string functionName)
    {
        return this.GetSemanticFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string skillName, string functionName)
    {
        if (this.HasSemanticFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string skillName, string functionName)
    {
        if (this.HasNativeFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string functionName)
    {
        return this.GetNativeFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
    {
        var result = new FunctionsView();

        if (includeSemantic)
        {
            foreach (var skill in this._skillCollection)
            {
                foreach (KeyValuePair<string, ISKFunction> f in skill.Value)
                {
                    if (f.Value.IsSemantic) { result.AddFunction(f.Value.Describe()); }
                }
            }
        }

        if (!includeNative) { return result; }

        foreach (var skill in this._skillCollection)
        {
            foreach (KeyValuePair<string, ISKFunction> f in skill.Value)
            {
                if (!f.Value.IsSemantic) { result.AddFunction(f.Value.Describe()); }
            }
        }

        return result;
    }

    #region private ================================================================================

    private readonly ILogger _log = NullLogger.Instance;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _skillCollection;

    #endregion
}
