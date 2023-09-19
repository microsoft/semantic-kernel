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
    /// <summary>
    /// Collection of semantic skill names and function names, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public ConcurrentDictionary<string, List<FunctionView>> SemanticFunctions { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Collection of native skill names and function views, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public ConcurrentDictionary<string, List<FunctionView>> NativeFunctions { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Add a function to the list
    /// </summary>
    /// <param name="view">Function details</param>
    /// <returns>Current instance</returns>
    public FunctionsView AddFunction(FunctionView view)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        if (view.IsSemantic)
        {
            if (!this.SemanticFunctions.ContainsKey(view.SkillName))
            {
                this.SemanticFunctions[view.SkillName] = new();
            }

            this.SemanticFunctions[view.SkillName].Add(view);
        }
        else
        {
            if (!this.NativeFunctions.ContainsKey(view.SkillName))
            {
                this.NativeFunctions[view.SkillName] = new();
            }

            this.NativeFunctions[view.SkillName].Add(view);
        }
#pragma warning restore CS0618 // Type or member is obsolete

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
        var sf = this.SemanticFunctions.ContainsKey(skillName)
                 && this.SemanticFunctions[skillName]
                     .Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase));

        var nf = this.NativeFunctions.ContainsKey(skillName)
                 && this.NativeFunctions[skillName]
                     .Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase));

        if (sf && nf)
        {
            throw new AmbiguousMatchException("There are 2 functions with the same name, one native and one semantic");
        }

        return sf;
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
        var sf = this.SemanticFunctions.ContainsKey(skillName)
                 && this.SemanticFunctions[skillName]
                     .Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase));

        var nf = this.NativeFunctions.ContainsKey(skillName)
                 && this.NativeFunctions[skillName]
                     .Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase));

        if (sf && nf)
        {
            throw new AmbiguousMatchException("There are 2 functions with the same name, one native and one semantic");
        }

        return nf;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"Native = {this.NativeFunctions.Count}, Semantic = {this.SemanticFunctions.Count}";
}
