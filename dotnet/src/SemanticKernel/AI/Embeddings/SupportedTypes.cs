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
    /// <typeparam name="T">The type to check.</typeparam>
    /// <returns>true if the vector operations support this type.</returns>
    public static bool IsSupported<T>() =>
        typeof(T) == typeof(float) || typeof(T) == typeof(double);

    /// <summary>
    /// Determines whether a specified type is supported by the vector operations.
    /// </summary>
    /// <param name="type">The <see cref="Type"/> to check.</param>
    /// <returns>true if the vector operations support this type.</returns>
    public static bool IsSupported(Type type) =>
        type == typeof(float) || type == typeof(double);

    /// <summary>
    /// The collection of types supported by the vector operations.
    /// </summary>
    public static IEnumerable<Type> Types => s_types;

    /// <summary>
    /// Checks if a specified type is supported by the vector operations.
    /// </summary>
    /// <typeparam name="T">The type to check.</typeparam>
    /// <param name="callerName">Caller member name.</param>
    /// <exception cref="NotSupportedException">Throws if type is not supported.</exception>
    internal static void VerifyTypeSupported<T>([CallerMemberName] string callerName = "")
    {
        if (!IsSupported<T>())
        {
            ThrowTypeNotSupported<T>(callerName);
        }
    }

    #region internal ================================================================================

    /// <summary>
    /// Throws type not supported exception.
    /// </summary>
    /// <typeparam name="T">The unsupported type.</typeparam>
    /// <param name="callerName">Caller member name.</param>
    /// <exception cref="NotSupportedException">Throws if type is not supported.</exception>
    internal static void ThrowTypeNotSupported<T>([CallerMemberName] string callerName = "")
    {
        throw new NotSupportedException($"Type '{typeof(T).Name}' not supported by {callerName}. "
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
