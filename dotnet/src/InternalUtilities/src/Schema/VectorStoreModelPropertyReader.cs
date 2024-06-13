// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using JsonSchemaMapper;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains helpers for reading memory service model properties and their attributes.
/// </summary>
internal static class MemoryServiceModelPropertyReader
{
    /// <summary>Cache of property enumerations so that we don't incur reflection costs with each invocation.</summary>
    private static readonly Dictionary<Type, (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties)> s_propertiesCache = new();

    /// <summary>
    /// Find the properties with <see cref="MemoryRecordKeyAttribute"/>, <see cref="MemoryRecordDataAttribute"/> and <see cref="MemoryRecordVectorAttribute"/> attributes
    /// and verify that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vector properties are supported instead of just one.</param>
    /// <returns>The categorized properties.</returns>
    public static (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) FindProperties(Type type, bool supportsMultipleVectors)
    {
        // First check the cache.
        if (s_propertiesCache.TryGetValue(type, out var cachedProperties))
        {
            return cachedProperties;
        }

        PropertyInfo? keyProperty = null;
        List<PropertyInfo> dataProperties = new();
        List<PropertyInfo> vectorProperties = new();
        bool singleVectorPropertyFound = false;

        foreach (var property in type.GetProperties())
        {
            // Get Key property.
            if (property.GetCustomAttribute<MemoryRecordKeyAttribute>() is not null)
            {
                if (keyProperty is not null)
                {
                    throw new ArgumentException($"Multiple key properties found on type {type.FullName}.");
                }

                keyProperty = property;
            }

            // Get data properties.
            if (property.GetCustomAttribute<MemoryRecordDataAttribute>() is not null)
            {
                dataProperties.Add(property);
            }

            // Get Vector properties.
            if (property.GetCustomAttribute<MemoryRecordVectorAttribute>() is not null)
            {
                // Add all vector properties if we support multiple vectors.
                if (supportsMultipleVectors)
                {
                    vectorProperties.Add(property);
                }
                // Add only one vector property if we don't support multiple vectors.
                else if (!singleVectorPropertyFound)
                {
                    vectorProperties.Add(property);
                    singleVectorPropertyFound = true;
                }
                else
                {
                    throw new ArgumentException($"Multiple vector properties found on type {type.FullName} while only one is supported.");
                }
            }
        }

        // Check that we have a key property.
        if (keyProperty is null)
        {
            throw new ArgumentException($"No key property found on type {type.FullName}.");
        }

        // Check that we have one vector property if we don't have named vectors.
        if (!supportsMultipleVectors && !singleVectorPropertyFound)
        {
            throw new ArgumentException($"No vector property found on type {type.FullName}.");
        }

        // Update the cache.
        s_propertiesCache[type] = (keyProperty, dataProperties, vectorProperties);

        return (keyProperty, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Find the properties listed in the <paramref name="memoryRecordDefinition"/> on the <paramref name="type"/> and verify
    /// that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="memoryRecordDefinition">The property configuration.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vector properties are supported instead of just one.</param>
    /// <returns>The categorized properties.</returns>
    public static (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) FindProperties(Type type, MemoryRecordDefinition memoryRecordDefinition, bool supportsMultipleVectors)
    {
        PropertyInfo? keyProperty = null;
        List<PropertyInfo> dataProperties = new();
        List<PropertyInfo> vectorProperties = new();
        bool singleVectorPropertyFound = false;

        foreach (MemoryRecordProperty property in memoryRecordDefinition.Properties)
        {
            // Key.
            if (property is MemoryRecordKeyProperty keyPropertyInfo)
            {
                if (keyProperty is not null)
                {
                    throw new ArgumentException($"Multiple key properties specified for type {type.FullName}.");
                }

                keyProperty = type.GetProperty(keyPropertyInfo.PropertyName);
                if (keyProperty == null)
                {
                    throw new ArgumentException($"Key property '{keyPropertyInfo.PropertyName}' not found on type {type.FullName}.");
                }
            }
            // Data.
            else if (property is MemoryRecordDataProperty dataPropertyInfo)
            {
                var dataProperty = type.GetProperty(dataPropertyInfo.PropertyName);
                if (dataProperty == null)
                {
                    throw new ArgumentException($"Data property '{dataPropertyInfo.PropertyName}' not found on type {type.FullName}.");
                }

                dataProperties.Add(dataProperty);
            }
            // Vector.
            else if (property is MemoryRecordVectorProperty vectorPropertyInfo)
            {
                var vectorProperty = type.GetProperty(vectorPropertyInfo.PropertyName);
                if (vectorProperty == null)
                {
                    throw new ArgumentException($"Vector property '{vectorPropertyInfo.PropertyName}' not found on type {type.FullName}.");
                }

                // Add all vector properties if we support multiple vectors.
                if (supportsMultipleVectors)
                {
                    vectorProperties.Add(vectorProperty);
                }
                // Add only one vector property if we don't support multiple vectors.
                else if (!singleVectorPropertyFound)
                {
                    vectorProperties.Add(vectorProperty);
                    singleVectorPropertyFound = true;
                }
                else
                {
                    throw new ArgumentException($"Multiple vector properties configured for type {type.FullName} while only one is supported.");
                }
            }
            else
            {
                throw new ArgumentException($"Unknown property type '{property.GetType().FullName}' in memory record definition.");
            }
        }

        // Check that we have one vector property if we don't have named vectors.
        if (!supportsMultipleVectors && !singleVectorPropertyFound)
        {
            throw new ArgumentException($"No vector property configured for type {type.FullName}.");
        }

        return (keyProperty!, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(List<PropertyInfo> properties, HashSet<Type> supportedTypes, string propertyCategoryDescription)
    {
        foreach (var property in properties)
        {
            if (!supportedTypes.Contains(property.PropertyType))
            {
                var supportedTypesString = string.Join(", ", supportedTypes.Select(t => t.FullName));
                throw new ArgumentException($"{propertyCategoryDescription} properties must be one of the supported types: {supportedTypesString}. Type of {property.Name} is {property.PropertyType.FullName}.");
            }
        }
    }

    /// <summary>
    /// Get the serialized name of a property by first checking the <see cref="JsonPropertyNameAttribute"/> and then falling back to the property name.
    /// </summary>
    /// <param name="property">The property to retrieve a serialized name for.</param>
    /// <returns>The serialized name for the property.</returns>
    public static string GetSerializedPropertyName(PropertyInfo property)
    {
        return property.GetCustomAttribute<JsonPropertyNameAttribute>()?.Name ?? property.Name;
    }
}
