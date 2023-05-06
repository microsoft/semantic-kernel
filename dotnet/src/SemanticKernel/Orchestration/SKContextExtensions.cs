// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.SkillDefinition;

// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.Orchestration;

internal static class SKContextExtensions
{
    /// <summary>
    /// Simple extension method to check if a function is registered in the SKContext.
    /// </summary>
    /// <param name="context">The SKContext to check</param>
    /// <param name="skillName">The skill name</param>
    /// <param name="functionName">The function name</param>
    /// <param name="registeredFunction">The registered function, if found</param>
    internal static bool IsFunctionRegistered(this SKContext context, string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? registeredFunction)
    {
        context.ThrowIfSkillCollectionNotSet();

        return context.Skills!.TryGetNativeFunction(skillName, functionName, out registeredFunction) ||
               context.Skills.TryGetNativeFunction(functionName, out registeredFunction) ||
               context.Skills.TryGetSemanticFunction(skillName, functionName, out registeredFunction);
    }

    /// <summary>
    /// Ensures the context has a skill collection available
    /// </summary>
    /// <param name="context">SK execution context</param>
    internal static void ThrowIfSkillCollectionNotSet(this SKContext context)
    {
        if (context.Skills == null)
        {
            throw new KernelException(
                KernelException.ErrorCodes.SkillCollectionNotSet,
                "Skill collection not found in the context");
        }
    }
}
