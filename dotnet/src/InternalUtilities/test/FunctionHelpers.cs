// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.UnitTests;

/// <summary>Test helpers for working with native functions.</summary>
internal static class FunctionHelpers
{
    /// <summary>
    /// Invokes a function on a skill instance via the kernel.
    /// </summary>
    public static Task<SKContext> CallViaKernelAsync(
        object skillInstance,
        string methodName,
        params (string Name, string Value)[] variables)
    {
        var kernel = Kernel.Builder.Build();

        IDictionary<string, ISKFunction> funcs = kernel.ImportSkill(skillInstance);

        SKContext context = kernel.CreateNewContext();
        foreach ((string Name, string Value) pair in variables)
        {
            context.Variables.Set(pair.Name, pair.Value);
        }

        return funcs[methodName].InvokeAsync(context);
    }
}
