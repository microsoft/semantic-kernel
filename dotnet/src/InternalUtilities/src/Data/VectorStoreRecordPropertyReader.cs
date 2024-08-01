// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreRecordPropertyReader
{
    /// <summary>Cache of property enumerations so that we don't incur reflection costs with each invocation.</summary>
    private static readonly ConcurrentDictionary<Type, (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties)> s_singleVectorPropertiesCache = new();

    /// <summary>Cache of property enumerations so that we don't incur reflection costs with each invocation.</summary>
    private static readonly ConcurrentDictionary<Type, (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties)> s_multipleVectorsPropertiesCache = new();

    /// <summary>
    /// Split the given <paramref name="definition"/> into key, data and vector properties and verify that we have the expected numbers of each type.
    /// </summary>
    /// <param name="typeName">The name of the type that the definition relates to.</param>
    /// <param name="definition">The <see cref="VectorStoreRecordDefinition"/> to split.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vectors are supported.</param>
    /// <param name="requiresAtLeastOneVector">A value indicating whether we need at least one vector.</param>
    /// <returns>The properties on the <see cref="VectorStoreRecordDefinition"/> split into key, data and vector groupings.</returns>
    /// <exception cref="ArgumentException">Thrown if there are any validation failures with the provided <paramref name="definition"/>.</exception>
    public static (VectorStoreRecordKeyProperty KeyProperty, List<VectorStoreRecordDataProperty> DataProperties, List<VectorStoreRecordVectorProperty> VectorProperties) SplitDefinitionAndVerify(
        string typeName,
        VectorStoreRecordDefinition definition,
        bool supportsMultipleVectors,
        bool requiresAtLeastOneVector)
    {
        var keyProperties = definition.Properties.OfType<VectorStoreRecordKeyProperty>().ToList();

        if (keyProperties.Count > 1)
        {
            throw new ArgumentException($"Multiple key properties found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        var keyProperty = keyProperties.FirstOrDefault();
        var dataProperties = definition.Properties.OfType<VectorStoreRecordDataProperty>().ToList();
        var vectorProperties = definition.Properties.OfType<VectorStoreRecordVectorProperty>().ToList();

        if (keyProperty is null)
        {
            throw new ArgumentException($"No key property found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (requiresAtLeastOneVector && vectorProperties.Count == 0)
        {
            throw new ArgumentException($"No vector property found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (!supportsMultipleVectors && vectorProperties.Count > 1)
        {
            throw new ArgumentException($"Multiple vector properties found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        return (keyProperty, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Find the properties with <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/> attributes
    /// and verify that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vector properties are supported instead of just one.</param>
    /// <returns>The categorized properties.</returns>
    public static (PropertyInfo KeyProperty, List<PropertyInfo> DataProperties, List<PropertyInfo> VectorProperties) FindProperties(Type type, bool supportsMultipleVectors)
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
    public static (PropertyInfo KeyProperty, List<PropertyInfo> DataProperties, List<PropertyInfo> VectorProperties) FindProperties(Type type, VectorStoreRecordDefinition vectorStoreRecordDefinition, bool supportsMultipleVectors)
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

                keyProperty = type.GetProperty(keyPropertyInfo.DataModelPropertyName);
                if (keyProperty == null)
                {
                    throw new ArgumentException($"Key property '{keyPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
                }
            }
            // Data.
            else if (property is VectorStoreRecordDataProperty dataPropertyInfo)
            {
                var dataProperty = type.GetProperty(dataPropertyInfo.DataModelPropertyName);
                if (dataProperty == null)
                {
                    throw new ArgumentException($"Data property '{dataPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
                }

                dataProperties.Add(dataProperty);
            }
            // Vector.
            else if (property is VectorStoreRecordVectorProperty vectorPropertyInfo)
            {
                var vectorProperty = type.GetProperty(vectorPropertyInfo.DataModelPropertyName);
                if (vectorProperty == null)
                {
                    throw new ArgumentException($"Vector property '{vectorPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
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

        // Key property.
        var keyAttribute = properties.KeyProperty.GetCustomAttribute<VectorStoreRecordKeyAttribute>();
        definitionProperties.Add(new VectorStoreRecordKeyProperty(properties.KeyProperty.Name, properties.KeyProperty.PropertyType) { StoragePropertyName = keyAttribute!.StoragePropertyName });

        // Data properties.
        foreach (var dataProperty in properties.DataProperties)
        {
            var dataAttribute = dataProperty.GetCustomAttribute<VectorStoreRecordDataAttribute>();
            if (dataAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordDataProperty(dataProperty.Name, dataProperty.PropertyType)
                {
                    IsFilterable = dataAttribute.IsFilterable,
                    IsFullTextSearchable = dataAttribute.IsFullTextSearchable,
                    StoragePropertyName = dataAttribute.StoragePropertyName
                });
            }
        }

        // Vector properties.
        foreach (var vectorProperty in properties.VectorProperties)
        {
            var vectorAttribute = vectorProperty.GetCustomAttribute<VectorStoreRecordVectorAttribute>();
            if (vectorAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordVectorProperty(vectorProperty.Name, vectorProperty.PropertyType)
                {
                    Dimensions = vectorAttribute.Dimensions,
                    IndexKind = vectorAttribute.IndexKind,
                    DistanceFunction = vectorAttribute.DistanceFunction,
                    StoragePropertyName = vectorAttribute.StoragePropertyName
                });
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
    /// <param name="supportEnumerable">A value indicating whether <see cref="IEnumerable{T}"/> versions of all the types should also be supported.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(List<PropertyInfo> properties, HashSet<Type> supportedTypes, string propertyCategoryDescription, bool? supportEnumerable = false)
    {
        var supportedEnumerableTypes = supportEnumerable == true
            ? supportedTypes
            : [];

        VerifyPropertyTypes(properties, supportedTypes, supportedEnumerableTypes, propertyCategoryDescription);
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="supportedEnumerableTypes">A set of supported types that the provided enumerable properties may use as their element type.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(List<PropertyInfo> properties, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableTypes, string propertyCategoryDescription)
    {
        foreach (var property in properties)
        {
            VerifyPropertyType(property.Name, property.PropertyType, supportedTypes, supportedEnumerableTypes, propertyCategoryDescription);
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
        var supportedEnumerableTypes = supportEnumerable == true
            ? supportedTypes
            : [];

        VerifyPropertyTypes(properties, supportedTypes, supportedEnumerableTypes, propertyCategoryDescription);
    }

    /// <summary>
    /// Verify that the given properties are of the supported types.
    /// </summary>
    /// <param name="properties">The properties to check.</param>
    /// <param name="supportedTypes">A set of supported types that the provided properties may have.</param>
    /// <param name="supportedEnumerableTypes">A set of supported types that the provided enumerable properties may use as their element type.</param>
    /// <param name="propertyCategoryDescription">A description of the category of properties being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if any of the properties are not in the given set of types.</exception>
    public static void VerifyPropertyTypes(IEnumerable<VectorStoreRecordProperty> properties, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableTypes, string propertyCategoryDescription)
    {
        foreach (var property in properties)
        {
            VerifyPropertyType(property.DataModelPropertyName, property.PropertyType, supportedTypes, supportedEnumerableTypes, propertyCategoryDescription);
        }
    }

    /// <summary>
    /// Verify that the given property is of the supported types.
    /// </summary>
    /// <param name="propertyName">The name of the property being checked. Used for error messaging.</param>
    /// <param name="propertyType">The type of the property being checked.</param>
    /// <param name="supportedTypes">A set of supported types that the provided property may have.</param>
    /// <param name="supportedEnumerableTypes">A set of supported types that the provided property may use as its element type if it's enumerable.</param>
    /// <param name="propertyCategoryDescription">A description of the category of property being checked. Used for error messaging.</param>
    /// <exception cref="ArgumentException">Thrown if the property is not in the given set of types.</exception>
    public static void VerifyPropertyType(string propertyName, Type propertyType, HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableTypes, string propertyCategoryDescription)
    {
        // Add shortcut before testing all the more expensive scenarios.
        if (supportedTypes.Contains(propertyType))
        {
            return;
        }

        // Check all collection scenarios and get stored type.
        if (supportedEnumerableTypes.Count > 0 && typeof(IEnumerable).IsAssignableFrom(propertyType))
        {
            var typeToCheck = propertyType switch
            {
                IEnumerable => typeof(object),
                var enumerableType when enumerableType.IsGenericType && enumerableType.GetGenericTypeDefinition() == typeof(IEnumerable<>) => enumerableType.GetGenericArguments()[0],
                var arrayType when arrayType.IsArray => arrayType.GetElementType()!,
                var interfaceType when interfaceType.GetInterfaces().FirstOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>)) is Type enumerableInterface =>
                    enumerableInterface.GetGenericArguments()[0],
                _ => propertyType
            };

            if (!supportedEnumerableTypes.Contains(typeToCheck))
            {
                var supportedEnumerableElementTypesString = string.Join(", ", supportedEnumerableTypes!.Select(t => t.FullName));
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
    /// Get the JSON property name of a property by using the <see cref="JsonPropertyNameAttribute"/> if available, otherwise
    /// using the <see cref="JsonNamingPolicy"/> if available, otherwise falling back to the property name.
    /// The provided <paramref name="dataModel"/> may not actually contain the property, e.g. when the user has a data model that
    /// doesn't resemble the stored data and where they are using a custom mapper.
    /// </summary>
    /// <param name="property">The property to retrieve a storage name for.</param>
    /// <param name="dataModel">The data model type that the property belongs to.</param>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <returns>The JSON storage property name.</returns>
    public static string GetJsonPropertyName(VectorStoreRecordProperty property, Type dataModel, JsonSerializerOptions options)
    {
        var propertyInfo = dataModel.GetProperty(property.DataModelPropertyName);

        if (propertyInfo != null)
        {
            var jsonPropertyNameAttribute = propertyInfo.GetCustomAttribute<JsonPropertyNameAttribute>();
            if (jsonPropertyNameAttribute is not null)
            {
                return jsonPropertyNameAttribute.Name;
            }
        }

        if (options.PropertyNamingPolicy is not null)
        {
            return options.PropertyNamingPolicy.ConvertName(property.DataModelPropertyName);
        }

        return property.DataModelPropertyName;
    }

    /// <summary>
    /// Get the JSON property name of a property by using the <see cref="JsonPropertyNameAttribute"/> if available, otherwise
    /// using the <see cref="JsonNamingPolicy"/> if available, otherwise falling back to the property name.
    /// </summary>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <param name="property">The property to retrieve a storage name for.</param>
    /// <returns>The JSON storage property name.</returns>
    public static string GetJsonPropertyName(JsonSerializerOptions options, PropertyInfo property)
    {
        var jsonPropertyNameAttribute = property.GetCustomAttribute<JsonPropertyNameAttribute>();
        if (jsonPropertyNameAttribute is not null)
        {
            return jsonPropertyNameAttribute.Name;
        }

        if (options.PropertyNamingPolicy is not null)
        {
            return options.PropertyNamingPolicy.ConvertName(property.Name);
        }

        return property.Name;
    }

    /// <summary>
    /// Build a map of property names to the names under which they should be saved in storage if using JSON serialization.
    /// </summary>
    /// <param name="properties">The properties to build the map for.</param>
    /// <param name="dataModel">The data model type that the property belongs to.</param>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <returns>The map from property names to the names under which they should be saved in storage if using JSON serialization.</returns>
    public static Dictionary<string, string> BuildPropertyNameToJsonPropertyNameMap(
        (VectorStoreRecordKeyProperty keyProperty, List<VectorStoreRecordDataProperty> dataProperties, List<VectorStoreRecordVectorProperty> vectorProperties) properties,
        Type dataModel,
        JsonSerializerOptions options)
    {
        var jsonPropertyNameMap = new Dictionary<string, string>();
        jsonPropertyNameMap.Add(properties.keyProperty.DataModelPropertyName, GetJsonPropertyName(properties.keyProperty, dataModel, options));

        foreach (var dataProperty in properties.dataProperties)
        {
            jsonPropertyNameMap.Add(dataProperty.DataModelPropertyName, GetJsonPropertyName(dataProperty, dataModel, options));
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            jsonPropertyNameMap.Add(vectorProperty.DataModelPropertyName, GetJsonPropertyName(vectorProperty, dataModel, options));
        }

        return jsonPropertyNameMap;
    }

    /// <summary>
    /// Build a map of property names to the names under which they should be saved in storage if using JSON serialization.
    /// </summary>
    /// <param name="properties">The properties to build the map for.</param>
    /// <param name="dataModel">The data model type that the property belongs to.</param>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <returns>The map from property names to the names under which they should be saved in storage if using JSON serialization.</returns>
    public static Dictionary<string, string> BuildPropertyNameToJsonPropertyNameMap(
        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties,
        Type dataModel,
        JsonSerializerOptions options)
    {
        var jsonPropertyNameMap = new Dictionary<string, string>();
        jsonPropertyNameMap.Add(properties.keyProperty.Name, GetJsonPropertyName(options, properties.keyProperty));

        foreach (var dataProperty in properties.dataProperties)
        {
            jsonPropertyNameMap.Add(dataProperty.Name, GetJsonPropertyName(options, dataProperty));
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            jsonPropertyNameMap.Add(vectorProperty.Name, GetJsonPropertyName(options, vectorProperty));
        }

        return jsonPropertyNameMap;
    }

    /// <summary>
    /// Build a map of property names to the names under which they should be saved in storage, for the given properties.
    /// </summary>
    /// <param name="properties">The properties to build the map for.</param>
    /// <returns>The map from property names to the names under which they should be saved in storage.</returns>
    public static Dictionary<string, string> BuildPropertyNameToStorageNameMap((VectorStoreRecordKeyProperty keyProperty, List<VectorStoreRecordDataProperty> dataProperties, List<VectorStoreRecordVectorProperty> vectorProperties) properties)
    {
        var storagePropertyNameMap = new Dictionary<string, string>();
        storagePropertyNameMap.Add(properties.keyProperty.DataModelPropertyName, properties.keyProperty.StoragePropertyName ?? properties.keyProperty.DataModelPropertyName);

        foreach (var dataProperty in properties.dataProperties)
        {
            storagePropertyNameMap.Add(dataProperty.DataModelPropertyName, dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName);
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            storagePropertyNameMap.Add(vectorProperty.DataModelPropertyName, vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName);
        }

        return storagePropertyNameMap;
    }
}
