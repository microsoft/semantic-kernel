// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once CheckNamespace // Extension methods

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
    internal static bool IsFunctionRegistered(this SKContext context, string skillName, string functionName, out ISKFunction? registeredFunction)
    {
        context.ThrowIfSkillCollectionNotSet();

        if (context.Skills!.HasNativeFunction(skillName, functionName))
        {
            registeredFunction = context.Skills.GetNativeFunction(skillName, functionName);
            return true;
        }

        if (context.Skills.HasNativeFunction(functionName))
        {
            registeredFunction = context.Skills.GetNativeFunction(functionName);
            return true;
        }

        if (context.Skills.HasSemanticFunction(skillName, functionName))
        {
            registeredFunction = context.Skills.GetSemanticFunction(skillName, functionName);
            return true;
        }

        registeredFunction = null;
        return false;
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
