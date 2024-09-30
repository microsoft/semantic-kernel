// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains helper methods to map between storage and data models.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreRecordMapping
{
    /// <summary>
    /// Build a list of properties with their values from the given data model properties and storage values.
    /// </summary>
    /// <typeparam name="TStorageType">The type of the storage properties.</typeparam>
    /// <param name="dataModelPropertiesInfo"><see cref="PropertyInfo"/> objects listing the properties on the data model to get values for.</param>
    /// <param name="dataModelToStorageNameMapping">Storage property names keyed by data property names.</param>
    /// <param name="storageValues">A dictionary of storage values by storage property name.</param>
    /// <param name="storageValueConverter">An optional function to convert the storage property values to data property values.</param>
    /// <returns>The list of data property objects and their values.</returns>
    public static IEnumerable<KeyValuePair<PropertyInfo, object?>> BuildPropertiesInfoWithValues<TStorageType>(
        IEnumerable<PropertyInfo> dataModelPropertiesInfo,
        IDictionary<string, string> dataModelToStorageNameMapping,
        IDictionary<string, TStorageType> storageValues,
        Func<TStorageType, Type, object?>? storageValueConverter = null)
    {
        foreach (var propertyInfo in dataModelPropertiesInfo)
        {
            if (dataModelToStorageNameMapping.TryGetValue(propertyInfo.Name, out var storageName) &&
                storageValues.TryGetValue(storageName, out var storageValue))
            {
                if (storageValueConverter is not null)
                {
                    var convertedStorageValue = storageValueConverter(storageValue, propertyInfo.PropertyType);
                    yield return new KeyValuePair<PropertyInfo, object?>(propertyInfo, convertedStorageValue);
                }
                else
                {
                    yield return new KeyValuePair<PropertyInfo, object?>(propertyInfo, (object?)storageValue);
                }
            }
        }
    }

    /// <summary>
    /// Set the given list of properties with their values on the given object.
    /// </summary>
    /// <typeparam name="TRecord">The type of the target object.</typeparam>
    /// <param name="record">The target object to set the property values on.</param>
    /// <param name="propertiesInfoWithValues">A list of properties and their values to set.</param>
    public static void SetPropertiesOnRecord<TRecord>(
        TRecord record,
        IEnumerable<KeyValuePair<PropertyInfo, object?>> propertiesInfoWithValues)
            where TRecord : class
    {
        foreach (var propertyInfoWithValue in propertiesInfoWithValues)
        {
            propertyInfoWithValue.Key.SetValue(record, propertyInfoWithValue.Value);
        }
    }

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

        if (requiredEnumerable.IsGenericType)
        {
            var genericTypeDefinition = requiredEnumerable.GetGenericTypeDefinition();
            if (genericTypeDefinition == typeof(ICollection<>) ||
                genericTypeDefinition == typeof(IEnumerable<>) ||
                genericTypeDefinition == typeof(IList<>) ||
                genericTypeDefinition == typeof(IReadOnlyCollection<>) ||
                genericTypeDefinition == typeof(IReadOnlyList<>))
            {
                var genericMemberType = requiredEnumerable.GetGenericArguments()[0];
                var listType = typeof(List<>).MakeGenericType(genericMemberType);
                var enumerableType = typeof(IEnumerable<>).MakeGenericType(genericMemberType);
                var constructor = listType.GetConstructor([enumerableType]);
                return constructor!.Invoke([input]);
            }
        }

        if (requiredEnumerable == typeof(IEnumerable))
        {
            return input;
        }

        if (typeof(IList).IsAssignableFrom(requiredEnumerable))
        {
            var publicParameterlessConstructor = requiredEnumerable.GetConstructor([]);
            if (publicParameterlessConstructor is not null)
            {
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
