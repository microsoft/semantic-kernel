// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// A function view is a read-only representation of a function.
/// </summary>
/// <param name="Name">Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}</param>
/// <param name="SkillName">Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}</param>
/// <param name="Description">Function description. The description is used in combination with embeddings when searching relevant functions.</param>
/// <param name="Parameters">Optional list of function parameters</param>
public sealed record FunctionView(
    string Name,
    string SkillName,
    string Description = "",
    IReadOnlyList<ParameterView>? Parameters = null)
{
    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();
}
