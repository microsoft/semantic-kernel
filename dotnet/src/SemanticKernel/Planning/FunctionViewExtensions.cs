// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

internal static class FunctionViewExtensions
{
    internal static string ToManualString(this FunctionView function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(p => $"    - {p.Name}: {p.Description}"));
        return $"  {function.SkillName}.{function.Name}:\n    description: {function.Description}\n    inputs:\n{inputs}";
    }

    internal static string ToFunctionName(this FunctionView function)
    {
        return $"{function.SkillName}.{function.Name}";
    }
}
