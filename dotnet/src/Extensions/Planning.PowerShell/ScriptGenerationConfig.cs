// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

public class ScriptGenerationConfig
{
    /// <summary>
    /// A list of skills to exclude from the script generation request.
    /// </summary>
    public HashSet<string> ExcludedSkills { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the script generation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();
}
