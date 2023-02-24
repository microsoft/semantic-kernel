// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Optional attribute to set the name used for the function in the skill collection.
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionNameAttribute : Attribute
{
    /// <summary>
    /// Function name
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Tag a C# function as a native function available to SK.
    /// </summary>
    /// <param name="name">Function name</param>
    public SKFunctionNameAttribute(string name)
    {
        Verify.ValidFunctionName(name);
        this.Name = name;
    }
}
