// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

internal static class SKContextExtensions
{
    internal static string GetFunctionsManual(this SKContext context, PowerShellPlannerConfig config)
    {
        var functions = context.GetAvailableFunctions(config);

        return string.Join("\n\n", functions.Select(f => f.ToManualString()));
    }

    internal static IOrderedEnumerable<FunctionView> GetAvailableFunctions(this SKContext context, PowerShellPlannerConfig config)
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
