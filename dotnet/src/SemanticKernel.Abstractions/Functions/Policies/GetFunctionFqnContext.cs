// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Context for the <see cref="FunctionNamePolicy.GetFunctionFqn"/> method.
/// </summary>
/// <param name="functionName">The function name.</param>
[Experimental("SKEXP0001")]
public class GetFunctionFqnContext(string functionName)
{
    /// <summary>
    /// Gets or sets the plugin name.
    /// </summary>
    public string? PluginName { get; set; }

    /// <summary>
    /// Gets or sets the function name.
    /// </summary>
    public string FunctionName { get; set; } = functionName;
}
