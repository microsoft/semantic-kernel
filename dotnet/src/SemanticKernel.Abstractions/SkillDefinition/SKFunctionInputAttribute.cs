// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Attribute to describe the main parameter required by a native function,
/// e.g. the first "string" parameter, if the function requires one.
/// </summary>
/// <remarks>
/// The class has no constructor and requires the use of setters for readability.
/// e.g.
/// Readable:     [SKFunctionInput(Description = "...", DefaultValue = "...")]
/// Not readable: [SKFunctionInput("...", "...")]
/// </remarks>
/// <example>
/// <code>
///   // No main parameter here, only context
///   public async Task WriteAsync(SKContext context
/// </code>
/// </example>
/// <example>
/// <code>
///   // "path" is the input parameter
///   [SKFunctionInput("Source file path")]
///   public async Task{string?} ReadAsync(string path, SKContext context
/// </code>
/// </example>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class SKFunctionInputAttribute : Attribute
{
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
        return new ParameterView
        {
            Name = "input",
            Description = this.Description,
            DefaultValue = this.DefaultValue
        };
    }
}
