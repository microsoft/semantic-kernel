// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Reflection;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data from the skill collection.
/// The data is mutable, but changes do not affect the skill collection.
/// The class can be used to create custom lists in case your scenario needs to.
/// </summary>
public sealed class FunctionsView : List<FunctionView>
{
    /// <summary>
    /// Add a function to the list
    /// </summary>
    /// <param name="view">Function details</param>
    /// <returns>Current instance</returns>
    public FunctionsView AddFunction(FunctionView view)
    {
        this.Add(view);

        return this;
    }

    /// <summary>
    /// Collection of semantic skill names and function names, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    [Obsolete("Property no longer avialble. Use Dictionary methods instead. Example `myFunctionsView['skillName']['functionName']`")]
    public ConcurrentDictionary<string, List<FunctionView>> SemanticFunctions { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Collection of native skill names and function views, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    [Obsolete("Property no longer avialble. Use Dictionary methods instead. Example `myFunctionsView['skillName']['functionName']`")]
    public ConcurrentDictionary<string, List<FunctionView>> NativeFunctions { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Returns true if the function specified is unique and semantic
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and semantic</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    [Obsolete("No longer distinguishes between native and semantic functions.")]
    public bool IsSemantic(string skillName, string functionName)
        => throw new NotImplementedException("FunctionsView no longer distinguishes between native and semantic functions.");

    /// <summary>
    /// Returns true if the function specified is unique and native
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and native</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    [Obsolete("No longer distinguishes between native and semantic functions. This will be removed in a future release.")]
    public bool IsNative(string skillName, string functionName)
        => throw new NotImplementedException("FunctionsView no longer distinguishes between native and semantic functions.");
}
