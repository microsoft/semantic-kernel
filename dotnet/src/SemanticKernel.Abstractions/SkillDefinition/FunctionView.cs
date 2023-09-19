// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to surface read-only function information.
/// </summary>
public sealed record FunctionView(string Name,
        string SkillName,
        string? Description = null)
{
    /// <summary>
    /// Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    public string Name { get; init; } = Name;

    /// <summary>
    /// Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    public string SkillName { get; init; } = SkillName;

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    public string Description { get; init; } = Description ?? string.Empty;

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Array.Empty<ParameterView>();

    #region Obsolete

    /// <summary>
    /// Whether the delegate points to a semantic function
    /// </summary>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    [SuppressMessage("Design", "CA1065:Do not raise exceptions in unexpected locations")]
    public bool IsSemantic => throw new NotImplementedException("Kernel no longer differentiates between Semantic and Native functions.");

    /// <summary>
    /// Whether the delegate is an asynchronous function
    /// </summary>
    [Obsolete("FunctionView.IsAsynchronous property no longer available.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    [SuppressMessage("Design", "CA1065:Do not raise exceptions in unexpected locations")]
    public bool IsAsynchronous => throw new NotImplementedException("FunctionView.IsAsynchronous property no longer available.");

    #endregion
}
