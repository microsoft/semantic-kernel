// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Attribute required to register native functions into the kernel.
/// The registration is required by the prompt templating engine and by the pipeline generator (aka planner).
/// The quality of the description affects the planner ability to reason about complex tasks.
/// The description is used both with LLM prompts and embedding comparisons.
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionAttribute : Attribute
{
    private string? _name = null;

    /// <summary>
    /// Function name, to be used to identify the function in a collection.
    /// </summary>
    public string? Name
    {
        get { return this._name; }
        set
        {
            Verify.ValidFunctionName(value);
            this._name = value;
        }
    }

    /// <summary>
    /// Function description, to be used by the planner to auto-discover functions.
    /// </summary>
    public string? Description { get; set; } = null;
}
