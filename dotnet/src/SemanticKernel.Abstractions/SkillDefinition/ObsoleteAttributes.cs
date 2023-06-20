// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

// TODO: Delete these attributes.

[Obsolete("This attribute is deprecated and will be removed in one of the next SK SDK versions. Name a parameter \"input\" or use `[SKName(\"input\")]` on the parameter.")]
[EditorBrowsable(EditorBrowsableState.Never)]
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionInputAttribute : Attribute
{
    public string Description { get; set; } = string.Empty;

    public string DefaultValue { get; set; } = string.Empty;

    public ParameterView ToParameterView() =>
        new()
        {
            Name = "input",
            Description = this.Description,
            DefaultValue = this.DefaultValue
        };
}

[Obsolete("This attribute is deprecated and will be removed in one of the next SK SDK versions. Use `[SKName(\"FunctionName\")]`.")]
[EditorBrowsable(EditorBrowsableState.Never)]
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionNameAttribute : Attribute
{
    public SKFunctionNameAttribute(string name)
    {
        Verify.ValidFunctionName(name);
        this.Name = name;
    }

    public string Name { get; }
}

[Obsolete("This attribute is deprecated and will be removed in one of the next SK SDK versions. Use the DescriptionAttribute, DefaultValueAttribute, and SKNameAttribute instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public sealed class SKFunctionContextParameterAttribute : Attribute
{
    private string _name = "";

    public string Name
    {
        get => this._name;
        set
        {
            Verify.ValidFunctionParamName(value);
            this._name = value;
        }
    }

    public string Description { get; set; } = string.Empty;

    public string DefaultValue { get; set; } = string.Empty;

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
