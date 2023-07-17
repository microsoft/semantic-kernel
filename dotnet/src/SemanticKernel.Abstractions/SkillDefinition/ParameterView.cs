// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data about parameters
/// for planner and related scenarios.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class ParameterView
{
    private string _name = "";

    /// <summary>
    /// Parameter name. Alphanumeric chars + "_" only.
    /// </summary>
    public string Name
    {
        get => this._name;
        set
        {
            Verify.ValidFunctionParamName(value);
            this._name = value;
        }
    }

    /// <summary>
    /// Parameter description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Default value when the value is not provided.
    /// </summary>
    public string DefaultValue { get; set; } = string.Empty;

    /// <summary>
    /// Constructor
    /// </summary>
    public ParameterView()
    {
    }

    /// <summary>
    /// Create a function parameter view, using information provided by the skill developer.
    /// </summary>
    /// <param name="name">Parameter name. The name must be alphanumeric (underscore is the only special char allowed).</param>
    /// <param name="description">Parameter description</param>
    /// <param name="defaultValue">Default parameter value, if not provided</param>
    public ParameterView(
        string name,
        string description,
        string defaultValue)
    {
        Verify.ValidFunctionParamName(name);

        this.Name = name;
        this.Description = description;
        this.DefaultValue = defaultValue;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrEmpty(this.Description)
        ? this.Name
        : $"{this.Name} ({this.Description})";
}
