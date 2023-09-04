// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.Structured.Extensions;

using System.Collections.Generic;
using System.Linq;
using SkillDefinition;


internal static class FunctionViewExtensions
{

    internal static string ToManualString(this FunctionsView functions)
    {
        List<FunctionView> availableFunctions = functions.SemanticFunctions
            .Concat(functions.NativeFunctions)
            .SelectMany(x => x.Value)
            .ToList();
        var functionsString = string.Join("\n", availableFunctions.Select(function => function.ToManualString()));
        return functionsString;
    }


    /// <summary>
    /// Create a manual-friendly string for a function.
    /// </summary>
    /// <param name="function">The function to create a manual-friendly string for.</param>
    /// <returns>A manual-friendly string for a function.</returns>
    internal static string ToManualString(this FunctionView function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(parameter =>
        {
            var defaultValueString = string.IsNullOrEmpty(parameter.DefaultValue) ? string.Empty : $" (default value: {parameter.DefaultValue})";
            return $"  - {parameter.Name}: {parameter.Description}{defaultValueString}";
        }));

        return $@"{function.ToFullyQualifiedName()}:
  description: {function.Description}
  inputs:
  {inputs}";
    }


    /// <summary>
    /// Create a fully qualified name for a function.
    /// </summary>
    /// <param name="function">The function to create a fully qualified name for.</param>
    /// <returns>A fully qualified name for a function.</returns>
    internal static string ToFullyQualifiedName(this FunctionView function) => $"{function.SkillName}.{function.Name}";


    /// <summary>
    /// Create a string for generating an embedding for a function.
    /// </summary>
    /// <param name="function">The function to create a string for generating an embedding for.</param>
    /// <returns>A string for generating an embedding for a function.</returns>
    internal static string ToEmbeddingString(this FunctionView function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(p => $"    - {p.Name}: {p.Description}"));
        return $"{function.Name}:\n  description: {function.Description}\n  inputs:\n{inputs}";
    }
}
