// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class used to copy and export data about parameters
/// for planner and related scenarios.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class ParameterView
{
    private string _name = string.Empty;

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
    public string? Description { get; set; }

    /// <summary>
    /// Default value when the value is not provided.
    /// </summary>
    public string? DefaultValue { get; set; }

    /// <summary>
    /// Parameter type.
    /// </summary>
    public ParameterViewType? Type { get; set; }

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
    /// <param name="type">Parameter type.</param>
    public ParameterView(
        string name,
        string? description = null,
        string? defaultValue = null,
        ParameterViewType? type = null)
    {
        this.Name = name;
        this.Description = description;
        this.DefaultValue = defaultValue;
        this.Type = type;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrEmpty(this.Description)
        ? this.Name
        : $"{this.Name} ({this.Description})";
}
