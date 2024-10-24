// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Shared Utilities used by Kernel Process Components
/// </summary>
public static class KernelProcessUtilities
{
    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericStepType = typeof(KernelProcessStep<>);
    /// <summary>
    /// The generic step type of a step process state
    /// </summary>
    public static readonly Type sStepWithoutStateTargetType = typeof(KernelProcessStepState);
    /// <summary>
    /// The generic step type of a step process state with custom properties
    /// </summary>
    public static readonly Type sStepWitObjectStateTargetType = typeof(KernelProcessStepState<>).MakeGenericType(typeof(object));

    /// <summary>
    /// Attempts to find an instance of <![CDATA['KernelProcessStep<>']]> within the provided types hierarchy.
    /// </summary>
    /// <param name="type">The type to examine.</param>
    /// <param name="genericStateType">The matching type if found, otherwise null.</param>
    /// <returns>True if a match is found, false otherwise.</returns>
    public static bool TryGetSubtypeOfStatefulStep(Type? type, out Type? genericStateType)
    {
        return type.TryGetSpecificGenericType(s_genericStepType, out genericStateType);
    }
    private static bool TryGetSpecificGenericType(this Type? type, Type specificType, out Type? genericOutputType)
    {
        while (type != null && type != typeof(object))
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == specificType)
            {
                genericOutputType = type;
                return true;
            }

            type = type.BaseType;
        }

        genericOutputType = null;
        return false;
    }
}
