// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides a read-only descriptive view of an <see cref="ISKFunction"/> in a specific plugin.
/// </summary>
/// <param name="Name">Name of the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}</param>
/// <param name="PluginName">Name of the plugin containing the function.</param>
/// <param name="Description">Function description. The description is used in combination with embeddings when searching relevant functions.</param>
/// <param name="Parameters">Optional list of function parameters</param>
/// <param name="ReturnParameter">Function return parameter view</param>
public sealed record FunctionView(
    string Name,
    string? PluginName = null,
    string? Description = null,
    IReadOnlyList<ParameterView>? Parameters = null,
    ReturnParameterView? ReturnParameter = null)
{
    /// <summary>Gets the function description.</summary>
    public string Description { get; init; } = Description ?? "";

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();

    /// <summary>
    /// Function output
    /// </summary>
    public ReturnParameterView ReturnParameter { get; init; } = ReturnParameter ?? new ReturnParameterView();
}
