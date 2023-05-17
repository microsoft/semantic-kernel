// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Attribute to describe the parameters required by a native function.
///
/// Note: the class has no ctor, to force the use of setters and keep the attribute use readable
/// e.g.
/// Readable:     [SKFunctionContextParameter(Name = "...", Description = "...", DefaultValue = "...")]
/// Not readable: [SKFunctionContextParameter("...", "...", "...")]
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public sealed class SKFunctionContextParameterAttribute : Attribute
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
    /// Creates a parameter view, using information from an instance of this class.
    /// </summary>
    /// <returns>Parameter view.</returns>
    public ParameterView ToParameterView()
    {
        if (string.IsNullOrWhiteSpace(this.Name))
        {
            throw new InvalidOperationException($"The {nameof(SKFunctionContextParameterAttribute)}'s Name must be non-null and not composed entirely of whitespace.");
        }

        return new ParameterView
        {
            Name = this.Name,
            Description = this.Description,
            DefaultValue = this.DefaultValue
        };
    }
}
