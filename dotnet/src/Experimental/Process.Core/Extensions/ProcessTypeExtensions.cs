// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;
namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Provides extension methods for <see cref="Type"/> instances related to process steps.
/// </summary>
internal static class ProcessTypeExtensions
{
    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericType = typeof(KernelProcessStep<>);

    /// <summary>
    /// Attempts to find an instance of <![CDATA['KernelProcessStep<>']]> within the provided types hierarchy.
    /// </summary>
    /// <param name="type">The type to examine.</param>
    /// <param name="genericStateType">The matching type if found, otherwise null.</param>
    /// <returns>True if a match is found, false otherwise.</returns>
    public static bool TryGetSubtypeOfStatefulStep(this Type? type, out Type? genericStateType)
    {
        while (type != null && type != typeof(object))
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == s_genericType)
            {
                genericStateType = type;
                return true;
            }

            type = type.BaseType;
        }

        genericStateType = null;
        return false;
    }
}
