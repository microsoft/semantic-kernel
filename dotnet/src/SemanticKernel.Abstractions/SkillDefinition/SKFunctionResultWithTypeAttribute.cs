// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Attribute to describe the value returned from a native function.
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionResultWithTypeAttribute : Attribute
{
    /// <summary>
    /// Parameter description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Gets the content type.
    /// </summary>
    public ContentType ContentType { get; set; } = ContentType.Text;

    /// <summary>
    /// Gets the payload body type. For use with content types such as JSON, XML, etc.
    /// Describes the outputs for the AI model, so it can retrieve nested properties.
    /// </summary>
    public Type BodyType { get; set; } = typeof(string);

    /// <summary>
    /// Gets a view of the content type expected to be returned by the function.
    /// </summary>
    public ContentView ToContentView()
    {
        return new ContentView(this.Description, default, this.ContentType, this.BodyType);
    }
}
