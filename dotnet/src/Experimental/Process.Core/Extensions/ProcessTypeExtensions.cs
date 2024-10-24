// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Provides extension methods for <see cref="Type"/> instances related to process steps.
/// </summary>
internal static class ProcessTypeExtensions
{
    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericStepType = typeof(KernelProcessStep<>);

    private static readonly Type s_genericStepBuilder = typeof(ProcessStepBuilder<>);

    /// <summary>
    /// Attempts to find an instance of <![CDATA['KernelProcessStep<>']]> within the provided types hierarchy.
    /// </summary>
    /// <param name="type">The type to examine.</param>
    /// <param name="genericStateType">The matching type if found, otherwise null.</param>
    /// <returns>True if a match is found, false otherwise.</returns>
    public static bool TryGetSubtypeOfStatefulStep(this Type? type, out Type? genericStateType)
    {
        return type.TryGetSpecificType(s_genericStepType, out genericStateType);
    }

    public static bool TryGetSubtypeOfStatefulStepBuilder(this Type? type, out Type? genericStateType)
    {
        return type.TryGetSpecificType(s_genericStepBuilder, out genericStateType);
    }

    private static bool TryGetSpecificType(this Type? type, Type specificType, out Type? genericOutputType)
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
