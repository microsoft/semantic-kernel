// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

internal static class SKContextExtensions
{
    internal static string GetFunctionsManual(
        this SKContext context,
        List<string>? excludedSkills = null,
        List<string>? excludedFunctions = null)
    {
        var functions = context.GetAvailableFunctions(excludedSkills, excludedFunctions);

        return string.Join("\n\n",
            functions.Select(
                x =>
                {
                    var inputs = string.Join("\n", x.Parameters.Select(p => $"    -${p.Name}: {p.Description}"));
                    return $"  {x.SkillName}.{x.Name}:\n    description: {x.Description}\n    inputs:\n{inputs}";
                }));
    }

    // TODO: support more strategies, e.g. searching for relevant functions (by goal, by user preferences, etc.)
    internal static List<FunctionView> GetAvailableFunctions(
        this SKContext context,
        List<string>? excludedSkills = null,
        List<string>? excludedFunctions = null)
    {
        excludedSkills ??= new();
        excludedFunctions ??= new();

        context.ThrowIfSkillCollectionNotSet();

        var functionsView = context.Skills!.GetFunctionsView();

        return functionsView.SemanticFunctions
            .Concat(functionsView.NativeFunctions)
            .SelectMany(x => x.Value)
            .Where(s => !excludedSkills.Contains(s.SkillName) && !excludedFunctions.Contains(s.Name))
            .ToList();
    }
}
