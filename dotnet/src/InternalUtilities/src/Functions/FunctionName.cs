// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function name.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class FunctionName
{
    /// <summary>
    /// The plugin name.
    /// </summary>
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionName"/> class.
    /// </summary>
    /// <param name="name">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    public FunctionName(string name, string? pluginName = null)
    {
        Verify.NotNull(name);

        this.Name = name;
        this.PluginName = pluginName;
    }

    /// <summary>
    /// Gets the fully-qualified name of the function.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="functionNameSeparator">The function name separator.</param>
    /// <returns>Fully-qualified name of the function.</returns>
    public static string ToFullyQualifiedName(string functionName, string? pluginName = null, string functionNameSeparator = "-")
    {
        return string.IsNullOrEmpty(pluginName) ? functionName : $"{pluginName}{functionNameSeparator}{functionName}";
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionName"/> class.
    /// </summary>
    /// <param name="fullyQualifiedName">Fully-qualified name of the function.</param>
    /// <param name="functionNameSeparator">The function name separator.</param>
    public static FunctionName Parse(string fullyQualifiedName, string functionNameSeparator = "-")
    {
        Verify.NotNull(fullyQualifiedName);

        string? pluginName = null;
        string functionName = fullyQualifiedName;

        int separatorPos = fullyQualifiedName.IndexOf(functionNameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = fullyQualifiedName.AsSpan(0, separatorPos).Trim().ToString();
            functionName = fullyQualifiedName.AsSpan(separatorPos + functionNameSeparator.Length).Trim().ToString();
        }

        return new FunctionName(name: functionName, pluginName: pluginName);
    }
}
