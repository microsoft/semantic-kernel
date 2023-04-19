// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Attribute to describe the main parameter required by a native function,
/// e.g. the first "string" parameter, if the function requires one.
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionInputWithTypeAttribute : Attribute
{
    /// <summary>
    /// Parameter description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Default value when the value is not provided.
    /// </summary>
    public object? DefaultValue { get; set; } = default;

    /// <summary>
    /// Gets the content type.
    /// </summary>
    public ContentType ContentType { get; set; } = ContentType.Text;

    /// <summary>
    /// Gets the payload body type. For use with content types such as JSON, XML, etc.
    /// Describes the outputs for the AI model, so it can retrieve nested properties.
    /// </summary>
    public Type BodyType { get; set; } = typeof(string);

    public ContentView ToContentView()
    {
        return new ContentView(this.Description, this.DefaultValue, this.ContentType, this.BodyType);
    }
}
