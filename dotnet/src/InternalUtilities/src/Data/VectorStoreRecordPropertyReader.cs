// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreRecordPropertyReader
{
    /// <summary>Cache of property enumerations so that we don't incur reflection costs with each invocation.</summary>
    private static readonly Dictionary<Type, (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties)> s_singleVectorPropertiesCache = new();

    /// <summary>Cache of property enumerations so that we don't incur reflection costs with each invocation.</summary>
    private static readonly Dictionary<Type, (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties)> s_multipleVectorsPropertiesCache = new();

    /// <summary>
    /// Find the properties with <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/> attributes
    /// and verify that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vector properties are supported instead of just one.</param>
    /// <returns>The categorized properties.</returns>
    public static (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) FindProperties(Type type, bool supportsMultipleVectors)
    {
        var cache = supportsMultipleVectors ? s_multipleVectorsPropertiesCache : s_singleVectorPropertiesCache;

        // First check the cache.
        if (cache.TryGetValue(type, out var cachedProperties))
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
            if (property.GetCustomAttribute<VectorStoreRecordKeyAttribute>() is not null)
            {
                if (keyProperty is not null)
                {
                    throw new ArgumentException($"Multiple key properties found on type {type.FullName}.");
                }

                keyProperty = property;
            }

            // Get data properties.
            if (property.GetCustomAttribute<VectorStoreRecordDataAttribute>() is not null)
            {
                dataProperties.Add(property);
            }

            // Get Vector properties.
            if (property.GetCustomAttribute<VectorStoreRecordVectorAttribute>() is not null)
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
        cache[type] = (keyProperty, dataProperties, vectorProperties);

        return (keyProperty, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Find the properties listed in the <paramref name="vectorStoreRecordDefinition"/> on the <paramref name="type"/> and verify
    /// that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="vectorStoreRecordDefinition">The property configuration.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vector properties are supported instead of just one.</param>
    /// <returns>The categorized properties.</returns>
    public static (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) FindProperties(Type type, VectorStoreRecordDefinition vectorStoreRecordDefinition, bool supportsMultipleVectors)
    {
        PropertyInfo? keyProperty = null;
        List<PropertyInfo> dataProperties = new();
        List<PropertyInfo> vectorProperties = new();
        bool singleVectorPropertyFound = false;

        foreach (VectorStoreRecordProperty property in vectorStoreRecordDefinition.Properties)
        {
            // Key.
            if (property is VectorStoreRecordKeyProperty keyPropertyInfo)
            {
                if (keyProperty is not null)
                {
                    throw new ArgumentException($"Multiple key properties configured for type {type.FullName}.");
                }

                keyProperty = type.GetProperty(keyPropertyInfo.PropertyName);
                if (keyProperty == null)
                {
                    throw new ArgumentException($"Key property '{keyPropertyInfo.PropertyName}' not found on type {type.FullName}.");
                }
            }
            // Data.
            else if (property is VectorStoreRecordDataProperty dataPropertyInfo)
            {
                var dataProperty = type.GetProperty(dataPropertyInfo.PropertyName);
                if (dataProperty == null)
                {
                    throw new ArgumentException($"Data property '{dataPropertyInfo.PropertyName}' not found on type {type.FullName}.");
                }

                dataProperties.Add(dataProperty);
            }
            // Vector.
            else if (property is VectorStoreRecordVectorProperty vectorPropertyInfo)
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
                throw new ArgumentException($"Unknown property type '{property.GetType().FullName}' in vector store record definition.");
            }
        }

        // Check that we have a key property.
        if (keyProperty is null)
        {
            throw new ArgumentException($"No key property configured for type {type.FullName}.");
        }

        // Check that we have one vector property if we don't have named vectors.
        if (!supportsMultipleVectors && !singleVectorPropertyFound)
        {
            throw new ArgumentException($"No vector property configured for type {type.FullName}.");
        }

        return (keyProperty!, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Create a <see cref="VectorStoreRecordDefinition"/> by reading the attributes on the properties of the given type.
    /// </summary>
    /// <param name="type">The type to create the definition for.</param>
    /// <param name="supportsMultipleVectors"><see langword="true"/> if the store supports multiple vectors, <see langword="false"/> otherwise.</param>
    /// <returns>The <see cref="VectorStoreRecordDefinition"/> based on the given type.</returns>
    public static VectorStoreRecordDefinition CreateVectorStoreRecordDefinitionFromType(Type type, bool supportsMultipleVectors)
    {
        var properties = FindProperties(type, supportsMultipleVectors);
        var definitionProperties = new List<VectorStoreRecordProperty>();

        definitionProperties.Add(new VectorStoreRecordKeyProperty(properties.keyProperty.Name));

        foreach (var dataProperty in properties.dataProperties)
        {
            var dataAttribute = dataProperty.GetCustomAttribute<VectorStoreRecordDataAttribute>();
            if (dataAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordDataProperty(dataProperty.Name)
                {
                    HasEmbedding = dataAttribute.HasEmbedding,
                    EmbeddingPropertyName = dataAttribute.EmbeddingPropertyName,
                });
            }
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            var vectorAttribute = vectorProperty.GetCustomAttribute<VectorStoreRecordVectorAttribute>();
            if (vectorAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordVectorProperty(vectorProperty.Name));
            }
        }

        return new VectorStoreRecordDefinition { Properties = definitionProperties };
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
