// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

public class ScriptPlannerConfig
{
    /// <summary>
    /// A list of skills to exclude from the script generation request.
    /// </summary>
    public HashSet<string> ExcludedSkills { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the script generation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();

    /// <summary>
    /// Optional callback to get a function by name.
    /// </summary>
    public Func<string, string, ISKFunction?>? GetSkillFunction { get; set; }
}
