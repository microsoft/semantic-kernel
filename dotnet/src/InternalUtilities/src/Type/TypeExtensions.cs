// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace System;

/// <summary>
/// Extensions methods for <see cref="System.Type"/>.
/// </summary>
internal static class TypeExtensions
{
    /// <summary>
    /// Tries to get the result type from a Task generic parameter.
    /// </summary>
    /// <param name="returnType"></param>
    /// <param name="resultType">The result type of the Task generic parameter.</param>
    /// <returns><c>true</c> if the result type was successfully retrieved; otherwise, <c>false</c>.</returns>
    public static bool TryGetTaskResultType(this Type? returnType, out Type resultType)
    {
        resultType = typeof(object);
        if (returnType is null)
        {
            return false;
        }

        if (returnType.IsGenericType && returnType.GetGenericTypeDefinition() == typeof(Task<>))
        {
            resultType = returnType.GetGenericArguments()[0];
            return true;
        }

        return false;
    }
}
