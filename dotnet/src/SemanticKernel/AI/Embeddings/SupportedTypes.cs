// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// Static class to identify which data types are supported by the vector operations.
/// </summary>
public static class SupportedTypes
{
    /// <summary>
    /// Determines whether a specified type is supported by the vector operations.
    /// </summary>
    /// <param name="type">The <see cref="Type"/> to check.</param>
    /// <returns>true if the vector operations support this type.</returns>
    public static bool IsSupported(Type type)
    {
        return s_types.Contains(type);
    }

    /// <summary>
    /// The collection of types supported by the vector operations.
    /// </summary>
    public static IEnumerable<Type> Types => s_types;

    /// <summary>
    /// Checks if a specified type is supported by the vector operations.
    /// </summary>
    /// <param name="type">The type to check.s</param>
    /// <param name="caller">Caller member name.</param>
    /// <exception cref="NotSupportedException">Throws if type is not supported.</exception>
    internal static void VerifyTypeSupported(Type type, [CallerMemberName] string caller = "")
    {
        if (!IsSupported(type))
        {
            ThrowTypeNotSupported(type, caller);
        }
    }

    #region internal ================================================================================

    /// <summary>
    /// Throws type not supported exception.
    /// </summary>
    /// <param name="type">The type to check.s</param>
    /// <param name="caller">Caller member name.</param>
    /// <exception cref="NotSupportedException">Throws if type is not supported.</exception>
    internal static void ThrowTypeNotSupported(Type type, [CallerMemberName] string caller = "")
    {
        throw new NotSupportedException($"Type '{type.Name}' not supported by {caller}. "
                                        + $"Supported types include: [ {ToString()} ]");
    }

    #endregion

    #region private ================================================================================

    private static readonly Type[] s_types = { typeof(float), typeof(double) };

    private static new string ToString()
    {
        return string.Join(", ", s_types.Select(t => t.Name).ToList());
    }

    #endregion
}
