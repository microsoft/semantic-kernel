// Copyright (c) Microsoft. All rights reserved.

using System.Linq;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel.SkillDefinition;

internal static class FunctionViewExtensions
{
    /// <summary>
    /// Create a manual-friendly string for a function.
    /// </summary>
    /// <param name="function">The function to create a manual-friendly string for.</param>
    /// <returns>A manual-friendly string for a function.</returns>
    internal static string ToManualString(this FunctionView function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(p => $"    - {p.Name}: {p.Description}"));
        return $"  {function.ToFullyQualifiedName()}:\n    description: {function.Description}\n    inputs:\n{inputs}";
    }

    /// <summary>
    /// Create a fully qualified name for a function.
    /// </summary>
    /// <param name="function">The function to create a fully qualified name for.</param>
    /// <returns>A fully qualified name for a function.</returns>
    internal static string ToFullyQualifiedName(this FunctionView function)
    {
        return $"{function.SkillName}.{function.Name}";
    }
}
