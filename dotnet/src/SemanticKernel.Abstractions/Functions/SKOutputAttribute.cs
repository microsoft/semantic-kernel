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
    public SKOutputAttribute(string description)
    {
        this.Description = description;
    }
    /// <summary>Gets the specified output description.</summary>
    public string Description { get; }
}
