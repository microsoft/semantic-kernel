// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data from the skill collection.
/// The data is mutable, but changes do not affect the skill collection.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class FunctionView
{
    /// <summary>
    /// Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    public string SkillName { get; }

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    public string Description { get; }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a function view.
    /// </summary>
    /// <param name="name">Function name</param>
    /// <param name="skillName">Skill name, e.g. the function namespace</param>
    /// <param name="description">Function description</param>
    /// <param name="parameters">List of function parameters provided by the skill developer</param>
    public FunctionView(
        string name,
        string skillName,
        string description,
        IList<ParameterView>? parameters = null)
    {
        this.Name = name;
        this.SkillName = skillName;
        this.Description = description;
        this.Parameters = parameters is not null
            ? new List<ParameterView>(parameters)
            : new List<ParameterView>(0);
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.Name} ({this.Description})";

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
