// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;

namespace System;

/// <summary>
/// Extensions methods for <see cref="System.Type"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class TypeExtensions
{
    /// <summary>
    /// Tries to get the result type from a generic parameter.
    /// </summary>
    /// <param name="returnType">Return type.</param>
    /// <param name="resultType">The result type of the Nullable generic parameter.</param>
    /// <returns><c>true</c> if the result type was successfully retrieved; otherwise, <c>false</c>.</returns>
    /// TODO [@teresaqhoang]: Issue #4202 Cache Generic Types Extraction - Handlebars
    public static bool TryGetGenericResultType(this Type? returnType, out Type resultType)
    {
        resultType = typeof(object);
        if (returnType is null)
        {
            return false;
        }

        if (returnType.IsGenericType)
        {
            Type genericTypeDef = returnType.GetGenericTypeDefinition();

            if (genericTypeDef == typeof(Task<>)
                || genericTypeDef == typeof(Nullable<>)
                || genericTypeDef == typeof(ValueTask<>))
            {
                resultType = returnType.GetGenericArguments()[0];
            }
            else if (genericTypeDef == typeof(IEnumerable<>)
                || genericTypeDef == typeof(IList<>)
                || genericTypeDef == typeof(ICollection<>))
            {
                resultType = typeof(List<>).MakeGenericType(returnType.GetGenericArguments()[0]);
            }
            else if (genericTypeDef == typeof(IDictionary<,>))
            {
                Type[] genericArgs = returnType.GetGenericArguments();
                resultType = typeof(Dictionary<,>).MakeGenericType(genericArgs[0], genericArgs[1]);
            }

            return true;
        }

        return false;
    }

    /// <summary>
    /// Returns a string with the type's name. If the type is generic, it also includes the type parameters in a readable format.
    /// </summary>
    /// <param name="type">Target type.</param>
    public static string GetFriendlyTypeName(this Type type)
    {
        if (type.IsGenericType)
        {
            string typeName = type.GetGenericTypeDefinition().Name;
            // Remove the `1, `2 etc from the type name which indicates the number of generic arguments  
            typeName = typeName.Substring(0, typeName.IndexOf('`', (int)StringComparison.CurrentCulture));
            string genericArgs = string.Join(", ", type.GetGenericArguments().Select(t => GetFriendlyTypeName(t)));
            return $"{typeName}<{genericArgs}>";
        }

        return type.Name;
    }
}
