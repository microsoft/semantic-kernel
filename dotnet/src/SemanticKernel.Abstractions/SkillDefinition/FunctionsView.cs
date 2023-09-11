// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data from the skill collection.
/// The data is mutable, but changes do not affect the skill collection.
/// The class can be used to create custom lists in case your scenario needs to.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class FunctionsView
{
    private object _lock = new();
    /// <summary>
    /// Collection of semantic skill names and function names, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public ConcurrentDictionary<string, List<FunctionView>> SemanticFunctions { get; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Collection of native skill names and function views, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public ConcurrentDictionary<string, List<FunctionView>> NativeFunctions { get; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Add a function to the list
    /// </summary>
    /// <param name="view">Function details</param>
    /// <returns>Current instance</returns>
    public FunctionsView AddFunction(FunctionView view)
    {
        lock (this._lock)
        {
            if (view.IsSemantic)
            {
                this.SemanticFunctions.GetOrAdd(view.SkillName, _ => new()).Add(view);
            }
            else
            {
                this.NativeFunctions.GetOrAdd(view.SkillName, _ => new()).Add(view);
            }
        }

        return this;
    }

    /// <summary>
    /// Returns true if the function specified is unique and semantic
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and semantic</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    public bool IsSemantic(string skillName, string functionName)
    {
        return this.IsFunctionCheck(skillName, functionName, nativeFunctionCheck: false);
    }

    /// <summary>
    /// Returns true if the function specified is unique and native
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and native</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    public bool IsNative(string skillName, string functionName)
    {
        return this.IsFunctionCheck(skillName, functionName, nativeFunctionCheck: true);
    }

    private bool IsFunctionCheck(string skillName, string functionName, bool nativeFunctionCheck)
    {
        this.SemanticFunctions.TryGetValue(skillName, out var semanticFunctions);
        var foundSemanticFunction = semanticFunctions?.Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase))
                                    ?? false;

        this.NativeFunctions.TryGetValue(skillName, out var nativeFunctions);
        var foundNativeFunction = nativeFunctions?.Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase))
                                  ?? false;

        if (foundSemanticFunction && foundNativeFunction)
        {
            throw new AmbiguousMatchException("There are 2 functions with the same name, one native and one semantic");
        }

        return (nativeFunctionCheck)
            ? foundNativeFunction
            : foundSemanticFunction;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"Native = {this.NativeFunctions.Count}, Semantic = {this.SemanticFunctions.Count}";
}
