// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>Overrides the default name used by a Semantic Kernel native function name or parameter.</summary>
/// <remarks>
/// By default, the method or parameter's name is used. If the method returns a task and ends with
/// "Async", by default the suffix is removed. This attribute can be used to override such heuristics.
/// </remarks>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Parameter, AllowMultiple = false)]
public sealed class SKNameAttribute : Attribute
{
    /// <summary>
    /// Initializes the attribute with the name to use.
    /// </summary>
    /// <param name="name">The name.</param>
    public SKNameAttribute(string name) => this.Name = name;

    /// <summary>Gets the specified name.</summary>
    public string Name { get; }
}
