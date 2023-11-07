// Copyright (c) Microsoft. All rights reserved.

using System;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Attribute to define the output of a native function.
/// </summary>
/// <remarks>
/// Intended to be used as part of the prompt describing the function to the model.
/// </remarks>
[AttributeUsage(AttributeTargets.ReturnValue, AllowMultiple = false)]
public sealed class SKOutputAttribute : Attribute
{
    /// <summary>
    /// Initializes the attribute with its (native function return) type and semantic description.
    /// </summary>
    /// <param name="description">The semantic description of the output.</param>
    /// <param name="type">Function output return type</param>
    /// <param name="range">The range out output included and excluded.</param>
    public SKOutputAttribute(string description, string type, string range)
    {
        this.Description = description;
        this.Type = type;
        this.Range = range;
    }
    /// <summary>Gets the specified output description.</summary>
    public string Description { get; }

    /// <summary>Gets the specified output return type.</summary>
    public string Type { get; }

    /// <summary>Gets the specified output range.</summary>
    public string Range { get; }
}
