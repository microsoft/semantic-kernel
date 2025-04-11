// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains helper methods to map between storage and data models.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreRecordMapping
{
    /// <summary>
    /// Create an enumerable of the required type from the input enumerable.
    /// </summary>
    /// <typeparam name="T">The type of elements in the input enumerable.</typeparam>
    /// <param name="input">The input enumerable to convert.</param>
    /// <param name="requiredEnumerable">The type to convert to.</param>
    /// <returns>The new enumerable in the required type.</returns>
    /// <exception cref="NotSupportedException">Thrown when a target type is requested that is not supported.</exception>
    public static object? CreateEnumerable<T>(IEnumerable<T> input, Type requiredEnumerable)
    {
        if (input is null)
        {
            return null;
        }

        // If the required type is an array, we can create an ArrayList of the required type, add all
        // items from the input, and then convert the ArrayList to an array of the required type.
        if (requiredEnumerable.IsArray)
        {
            if (requiredEnumerable.HasElementType)
            {
                var elementType = requiredEnumerable.GetElementType();

                var arrayList = new ArrayList();
                foreach (var item in input)
                {
                    arrayList.Add(item);
                }
                return arrayList.ToArray(elementType!);
            }

            return input.ToArray();
        }

        // If the required type is one of a few supported generic collection interface types that
        // are all implemented by List<>, we can create a List<> and add all items from the input.
        if (requiredEnumerable.IsGenericType)
        {
            var genericTypeDefinition = requiredEnumerable.GetGenericTypeDefinition();
            if (genericTypeDefinition == typeof(ICollection<>) ||
                genericTypeDefinition == typeof(IEnumerable<>) ||
                genericTypeDefinition == typeof(IList<>) ||
                genericTypeDefinition == typeof(IReadOnlyCollection<>) ||
                genericTypeDefinition == typeof(IReadOnlyList<>))
            {
                // Create a List<> using the generic type argument of the required enumerable.
                var genericMemberType = requiredEnumerable.GetGenericArguments()[0];
                var listType = typeof(List<>).MakeGenericType(genericMemberType);
                var enumerableType = typeof(IEnumerable<>).MakeGenericType(genericMemberType);
                var constructor = listType.GetConstructor([]);
                var list = (IList)constructor!.Invoke(null);

                // Add all items from the input into the new list.
                foreach (var item in input)
                {
                    list.Add(item);
                }
                return list;
            }
        }

        // If the required type is IEnumerable, we can return the input as is.
        if (requiredEnumerable == typeof(IEnumerable))
        {
            return input;
        }

        // If our required type implements IList and has a public parameterless constructor, we can
        // create an instance of it using reflection and add all items from the input.
        if (typeof(IList).IsAssignableFrom(requiredEnumerable))
        {
            var publicParameterlessConstructor = requiredEnumerable.GetConstructor([]);
            if (publicParameterlessConstructor is not null)
            {
                // Create the required type using the parameterless constructor and cast
                // it to an IList so we can add our input items.
                var list = (IList)publicParameterlessConstructor.Invoke(null);
                foreach (var item in input)
                {
                    list.Add(item);
                }
                return list;
            }
        }

        throw new NotSupportedException($"Type {requiredEnumerable.FullName} is not supported.");
    }
}
