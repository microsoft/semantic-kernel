// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using System.Linq;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

internal static class SKContextExtensions
{
    internal static string GetFunctionsManual(this SKContext context, ScriptGenerationConfig config)
    {
        var functions = context.GetAvailableFunctions(config);

        return string.Join("\n\n", functions.Select(f => f.ToManualString()));
    }

    internal static IOrderedEnumerable<FunctionView> GetAvailableFunctions(this SKContext context, ScriptGenerationConfig config)
    {
        var functionsView = context.Skills.GetFunctionsView();

        return functionsView.SemanticFunctions
            .Concat(functionsView.NativeFunctions)
            .SelectMany(x => x.Value)
            .Where(s => !config.ExcludedSkills.Contains(s.SkillName) && !config.ExcludedFunctions.Contains(s.Name))
            .OrderBy(x => x.SkillName)
            .ThenBy(x => x.Name);
    }
}
