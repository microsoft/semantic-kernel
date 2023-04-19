// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data from
/// <see cref="SKFunctionInputWithTypeAttribute"/>
/// and <see cref="SKFunctionResultWithTypeAttribute"/>
/// for planner and related scenarios.
/// </summary>
public sealed class ContentView
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
    /// Content type
    /// </summary>
    public ContentType ContentType { get; set; } = ContentType.Text;

    /// <summary>
    /// Body type
    /// </summary>
    public Type BodyType { get; set; } = typeof(string);

    /// <summary>
    /// Constructor
    /// </summary>
    public ContentView()
    {
    }

    /// <summary>
    /// Create a function parameter view, using information provided by the skill developer.
    /// </summary>
    /// <param name="description">Parameter description</param>
    /// <param name="defaultValue">Default parameter value, if not provided</param>
    /// <param name="contentType">Content type</param>
    /// <param name="bodyType">Body type</param>
    public ContentView(
        string description,
        object? defaultValue,
        ContentType contentType,
        Type bodyType)
    {
        this.Description = description;
        this.DefaultValue = defaultValue;
        this.ContentType = contentType;
        this.BodyType = bodyType;
    }
}
