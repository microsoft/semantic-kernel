// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;
internal sealed class FullyQualifiedFunctionName
{
    /// <summary>
    /// The plugin name.
    /// </summary>
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FullyQualifiedFunctionName"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    public FullyQualifiedFunctionName(string functionName, string? pluginName = null)
    {
        Verify.NotNull(functionName);

        this.FunctionName = functionName;
        this.PluginName = pluginName;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FullyQualifiedFunctionName"/> class.
    /// </summary>
    /// <param name="fullyQualifiedName">Fully-qualified name of the function.</param>
    /// <param name="functionNameSeparator">The function name separator.</param>
    public static FullyQualifiedFunctionName Parse(string fullyQualifiedName, string functionNameSeparator = "-")
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

        return new FullyQualifiedFunctionName(functionName: functionName, pluginName: pluginName);
    }
}
