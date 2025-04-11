// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains helpers for verifying the types of vector store record properties.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreRecordPropertyVerification
{
    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <param name="supportEnumerable">A value indicating whether <see cref="IEnumerable{T}"/> versions of all the types should also be supported.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(List<PropertyInfo> properties, HashSet<Type> supportedTypes, string propertyCategoryDescription, bool? supportEnumerable = false)
    {
        var supportedEnumerableElementTypes = supportEnumerable == true
            ? supportedTypes
            : [];

        VerifyPropertyTypes(properties, supportedTypes, supportedEnumerableElementTypes, propertyCategoryDescription);
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="supportedEnumerableElementTypes">A set of supported types that the provided enumerable properties may use as their element type.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(List<PropertyInfo> properties, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableElementTypes, string propertyCategoryDescription)
    {
        foreach (var property in properties)
        {
            VerifyPropertyType(property.Name, property.PropertyType, supportedTypes, supportedEnumerableElementTypes, propertyCategoryDescription);
        }
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <param name="supportEnumerable">A value indicating whether <see cref="IEnumerable{T}"/> versions of all the types should also be supported.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(IEnumerable<VectorStoreRecordProperty> properties, HashSet<Type> supportedTypes, string propertyCategoryDescription, bool? supportEnumerable = false)
    {
        var supportedEnumerableElementTypes = supportEnumerable == true
            ? supportedTypes
            : [];

        VerifyPropertyTypes(properties, supportedTypes, supportedEnumerableElementTypes, propertyCategoryDescription);
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="supportedEnumerableElementTypes">A set of supported types that the provided enumerable properties may use as their element type.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(IEnumerable<VectorStoreRecordProperty> properties, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableElementTypes, string propertyCategoryDescription)
    {
        foreach (var property in properties)
        {
            VerifyPropertyType(property.DataModelPropertyName, property.PropertyType, supportedTypes, supportedEnumerableElementTypes, propertyCategoryDescription);
        }
    }

    /// <summary>
    /// Verify that the given property is of the supported types.
    /// </summary>
    /// <param name="propertyName">The name of the property being checked. Used for error messaging.</param>
    /// <param name="propertyType">The type of the property being checked.</param>
    /// <param name="supportedTypes">A set of supported types that the provided property may have.</param>
    /// <param name="supportedEnumerableElementTypes">A set of supported types that the provided property may use as its element type if it's enumerable.</param>
    /// <param name="propertyCategoryDescription">A description of the category of property being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if the property is not in the given set of types.</exception>
    public static void VerifyPropertyType(string propertyName, Type propertyType, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableElementTypes, string propertyCategoryDescription)
    {
        // Add shortcut before testing all the more expensive scenarios.
        if (supportedTypes.Contains(propertyType))
        {
            return;
        }

        // Check all collection scenarios and get stored type.
        if (supportedEnumerableElementTypes.Count > 0 && IsSupportedEnumerableType(propertyType))
        {
            var typeToCheck = GetCollectionElementType(propertyType);

            if (!supportedEnumerableElementTypes.Contains(typeToCheck))
            {
                var supportedEnumerableElementTypesString = string.Join(", ", supportedEnumerableElementTypes!.Select(t => t.FullName));
                throw new ArgumentException($"Enumerable {propertyCategoryDescription} properties must have one of the supported element types: {supportedEnumerableElementTypesString}. Element type of the property '{propertyName}' is {typeToCheck.FullName}.");
            }
        }
        else
        {
            // if we got here, we know the type is not supported
            var supportedTypesString = string.Join(", ", supportedTypes.Select(t => t.FullName));
            throw new ArgumentException($"{propertyCategoryDescription} properties must be one of the supported types: {supportedTypesString}. Type of the property '{propertyName}' is {propertyType.FullName}.");
        }
    }

    /// <summary>
    /// Verify if the provided type is one of the supported Enumerable types.
    /// </summary>
    /// <param name="type">The type to check.</param>
    /// <returns><see langword="true"/> if the type is a supported Enumerable, <see langword="false"/> otherwise.</returns>
    public static bool IsSupportedEnumerableType(Type type)
    {
        if (type.IsArray || type == typeof(IEnumerable))
        {
            return true;
        }

#if NET6_0_OR_GREATER
        if (typeof(IList).IsAssignableFrom(type) && type.GetMemberWithSameMetadataDefinitionAs(s_objectGetDefaultConstructorInfo) != null)
#else
        if (typeof(IList).IsAssignableFrom(type) && type.GetConstructor(Type.EmptyTypes) != null)
#endif
        {
            return true;
        }

        if (type.IsGenericType)
        {
            var genericTypeDefinition = type.GetGenericTypeDefinition();
            if (genericTypeDefinition == typeof(ICollection<>) ||
                genericTypeDefinition == typeof(IEnumerable<>) ||
                genericTypeDefinition == typeof(IList<>) ||
                genericTypeDefinition == typeof(IReadOnlyCollection<>) ||
                genericTypeDefinition == typeof(IReadOnlyList<>))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Returns <see cref="Type"/> of collection elements.
    /// </summary>
    public static Type GetCollectionElementType(Type collectionType)
    {
        return collectionType switch
        {
            IEnumerable => typeof(object),
            var enumerableType when GetGenericEnumerableInterface(enumerableType) is Type enumerableInterface => enumerableInterface.GetGenericArguments()[0],
            var arrayType when arrayType.IsArray => arrayType.GetElementType()!,
            _ => collectionType
        };
    }

    [UnconditionalSuppressMessage("ReflectionAnalysis", "IL2070:UnrecognizedReflectionPattern",
        Justification = "The 'IEnumerable<>' Type must exist and so trimmer kept it. In which case " +
            "It also kept it on any type which implements it. The below call to GetInterfaces " +
            "may return fewer results when trimmed but it will return 'IEnumerable<>' " +
            "if the type implemented it, even after trimming.")]
    private static Type? GetGenericEnumerableInterface(Type type)
    {
        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(IEnumerable<>))
        {
            return type;
        }

        foreach (Type typeToCheck in type.GetInterfaces())
        {
            if (typeToCheck.IsGenericType && typeToCheck.GetGenericTypeDefinition() == typeof(IEnumerable<>))
            {
                return typeToCheck;
            }
        }

        return null;
    }

#if NET6_0_OR_GREATER
    private static readonly ConstructorInfo s_objectGetDefaultConstructorInfo = typeof(object).GetConstructor(Type.EmptyTypes)!;
#endif
}
