// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Planning;

namespace RepoUtils;

internal static class PlanExtensions
{
    internal static string ToPlanWithGoalString(this Plan plan, string indent = " ")
    {
        string goalHeader = $"{indent}Goal: {plan.Description}\n\n{indent}Steps:\n";

        return goalHeader + plan.ToPlanString();
    }
}
