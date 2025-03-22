// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a builder for a <see cref="VectorStoreRecordModel"/>.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordModelBuilder
{
    /// <summary>
    /// Options for building the model.
    /// </summary>
    protected VectorStoreRecordModelBuildingOptions Options { get; }

    /// <summary>
    /// The key properties of the record.
    /// </summary>
    protected List<VectorStoreRecordKeyPropertyModel> KeyProperties { get; } = [];

    /// <summary>
    /// The data properties of the record.
    /// </summary>
    protected List<VectorStoreRecordDataPropertyModel> DataProperties { get; } = [];

    /// <summary>
    /// The vector properties of the record.
    /// </summary>
    protected List<VectorStoreRecordVectorPropertyModel> VectorProperties { get; } = [];

    /// <summary>
    /// All properties of the record, of all types.
    /// </summary>
    protected IEnumerable<VectorStoreRecordPropertyModel> Properties => this.PropertyMap.Values;

    /// <summary>
    /// All properties of the record, of all types, indexed by their model name.
    /// </summary>
    protected Dictionary<string, VectorStoreRecordPropertyModel> PropertyMap { get; } = new();

    /// <summary>
    /// Constructs a new <see cref="VectorStoreRecordModelBuilder"/>.
    /// </summary>
    public VectorStoreRecordModelBuilder(VectorStoreRecordModelBuildingOptions options)
    {
        if (options.SupportsMultipleKeys && options.ReservedKeyStorageName is not null)
        {
            throw new ArgumentException($"{nameof(VectorStoreRecordModelBuildingOptions.ReservedKeyStorageName)} cannot be set when {nameof(VectorStoreRecordModelBuildingOptions.SupportsMultipleKeys)} is set.");
        }

        this.Options = options;
    }

    /// <summary>
    /// Builds and returns an <see cref="VectorStoreRecordModel"/> from the given <paramref name="clrType"/> and <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    [RequiresDynamicCode("Currently not compatible with NativeAOT code")]
    [RequiresUnreferencedCode("Currently not compatible with trimming")] // TODO
    public virtual VectorStoreRecordModel Build(Type clrType, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        var dynamicMapping = clrType.IsGenericType && clrType.GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>);

        if (!dynamicMapping)
        {
            this.ProcessClrTypeProperties(clrType, vectorStoreRecordDefinition);
        }

        if (vectorStoreRecordDefinition is null)
        {
            if (dynamicMapping)
            {
                throw new ArgumentException("Vector store record definition must be provided for dynamic mapping.");
            }
        }
        else
        {
            this.ProcessRecordDefinition(vectorStoreRecordDefinition, dynamicMapping ? null : clrType);
        }

        this.Customize();
        this.Finalize(clrType);

        return new(clrType, this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// As part of building the model, this method processes the properties of the given <paramref name="clrType"/>,
    /// detecting and reading attributes that affect the model. Not called for dynamic mapping scenarios.
    /// </summary>
    // TODO: This traverses the CLR type's properties, making it incompatible with trimming (and NativeAOT).
    // TODO: We could put [DynamicallyAccessedMembers] to preserve all properties, but that approach wouldn't
    // TODO: work with hierarchical data models (#10957).
    [RequiresUnreferencedCode("Traverses the CLR type's properties with reflection, so not compatible with trimming")]
    protected virtual void ProcessClrTypeProperties(Type clrType, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        // We want to allow the user-provided record definition to override anything configured via attributes
        // (allowing the same CLR type + attributes to be used with different record definitions).
        foreach (var clrProperty in clrType.GetProperties())
        {
            VectorStoreRecordPropertyModel? property = null;
            string? storageName = null;

            if (clrProperty.GetCustomAttribute<VectorStoreRecordKeyAttribute>() is { } keyAttribute)
            {
                var keyProperty = new VectorStoreRecordKeyPropertyModel(clrProperty.Name, clrProperty.PropertyType);
                this.KeyProperties.Add(keyProperty);
                storageName = keyAttribute.StoragePropertyName;
                property = keyProperty;
            }

            if (clrProperty.GetCustomAttribute<VectorStoreRecordDataAttribute>() is { } dataAttribute)
            {
                if (property is not null)
                {
                    // TODO: Test
                    throw new InvalidOperationException($"Only one of {nameof(VectorStoreRecordKeyAttribute)}, {nameof(VectorStoreRecordDataAttribute)} and {nameof(VectorStoreRecordVectorAttribute)} can be applied to a property.");
                }

                var dataProperty = new VectorStoreRecordDataPropertyModel(clrProperty.Name, clrProperty.PropertyType)
                {
                    IsFilterable = dataAttribute.IsFilterable,
                    IsFullTextSearchable = dataAttribute.IsFullTextSearchable,
                };

                this.DataProperties.Add(dataProperty);
                storageName = dataAttribute.StoragePropertyName;
                property = dataProperty;
            }

            if (clrProperty.GetCustomAttribute<VectorStoreRecordVectorAttribute>() is { } vectorAttribute)
            {
                if (property is not null)
                {
                    throw new InvalidOperationException($"Only one of {nameof(VectorStoreRecordKeyAttribute)}, {nameof(VectorStoreRecordDataAttribute)} and {nameof(VectorStoreRecordVectorAttribute)} can be applied to a property.");
                }

                var vectorProperty = new VectorStoreRecordVectorPropertyModel(clrProperty.Name, clrProperty.PropertyType)
                {
                    Dimensions = vectorAttribute.Dimensions,
                    IndexKind = vectorAttribute.IndexKind,
                    DistanceFunction = vectorAttribute.DistanceFunction
                };

                this.VectorProperties.Add(vectorProperty);
                storageName = vectorAttribute.StoragePropertyName;
                property = vectorProperty;
            }

            if (property is null)
            {
                // No mapping attribute was found, ignore this property.
                continue;
            }

            // If a custom serializer is used (e.g. JsonSerializer), it would ignore our own attributes/config, and
            // our model needs to be in sync with the serializer's behavior (for e.g. storage names in filters).
            // So we ignore the config here as well.
            // TODO: Consider throwing here instead of ignoring
            if (storageName is not null && !this.Options.UsesExternalSerializer)
            {
                property.StorageName = storageName;
            }

            property.ClrProperty = clrProperty;
            this.PropertyMap.Add(clrProperty.Name, property);
        }
    }

    /// <summary>
    /// As part of building the model, this method processes the given <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    protected virtual void ProcessRecordDefinition(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type? clrType)
    {
        foreach (VectorStoreRecordProperty definitionProperty in vectorStoreRecordDefinition.Properties)
        {
            if (!this.PropertyMap.TryGetValue(definitionProperty.DataModelPropertyName, out var property))
            {
                // Property wasn't found attribute-annotated on the CLR type, so we need to add it.

                // TODO: Make the property CLR type optional - no need to specify it when using a CLR type.
                switch (definitionProperty)
                {
                    case VectorStoreRecordKeyProperty definitionKeyProperty:
                        var keyProperty = new VectorStoreRecordKeyPropertyModel(definitionKeyProperty.DataModelPropertyName, definitionKeyProperty.PropertyType);
                        this.KeyProperties.Add(keyProperty);
                        this.PropertyMap.Add(definitionKeyProperty.DataModelPropertyName, keyProperty);
                        property = keyProperty;
                        break;
                    case VectorStoreRecordDataProperty definitionDataProperty:
                        var dataProperty = new VectorStoreRecordDataPropertyModel(definitionDataProperty.DataModelPropertyName, definitionDataProperty.PropertyType);
                        this.DataProperties.Add(dataProperty);
                        this.PropertyMap.Add(definitionDataProperty.DataModelPropertyName, dataProperty);
                        property = dataProperty;
                        break;
                    case VectorStoreRecordVectorProperty definitionVectorProperty:
                        var vectorProperty = new VectorStoreRecordVectorPropertyModel(definitionVectorProperty.DataModelPropertyName, definitionVectorProperty.PropertyType);
                        this.VectorProperties.Add(vectorProperty);
                        this.PropertyMap.Add(definitionVectorProperty.DataModelPropertyName, vectorProperty);
                        property = vectorProperty;
                        break;
                    default:
                        throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.");
                }

                if (clrType is not null)
                {
                    // If we have a CLR type (POCO, not dynamic mapping), get the CLR property's type and make sure it matches the definition.
                    // If the connector uses a custom serializer, we allow mismatches, assuming the serializer will take care of them.
                    var clrProperty = clrType.GetProperty(property.ModelName);

                    if (clrProperty is null)
                    {
                        if (!this.Options.UsesExternalSerializer)
                        {
                            throw new InvalidOperationException($"Property '{property.ModelName}' not found on CLR type '{clrType.FullName}'.");
                        }
                    }
                    else
                    {
                        property.ClrProperty = clrProperty;

                        if (clrProperty.PropertyType != property.ClrType && !this.Options.UsesExternalSerializer)
                        {
                            throw new InvalidOperationException($"Property '{property.ModelName}' has a different CLR type in the record definition and on the CLR type.");
                        }
                    }
                }
            }

            // If a custom serializer is used (e.g. JsonSerializer), it would ignore our own attributes/config, and
            // our model needs to be in sync with the serializer's behavior (for e.g. storage names in filters).
            // So we ignore the config here as well.
            // TODO: Consider throwing here instead of ignoring
            if (definitionProperty.StoragePropertyName is not null && !this.Options.UsesExternalSerializer)
            {
                property.StorageName = definitionProperty.StoragePropertyName;
            }

            switch (definitionProperty)
            {
                case VectorStoreRecordKeyProperty definitionKeyProperty:
                    if (property is not VectorStoreRecordKeyPropertyModel keyPropertyModel)
                    {
                        throw new InvalidOperationException($"Property '{property.ModelName}' is not a key property.");
                    }

                    break;

                case VectorStoreRecordDataProperty definitionDataProperty:
                    if (property is not VectorStoreRecordDataPropertyModel dataProperty)
                    {
                        throw new InvalidOperationException($"Property '{property.ModelName}' is not a data property.");
                    }

                    dataProperty.IsFilterable = definitionDataProperty.IsFilterable;
                    dataProperty.IsFullTextSearchable = definitionDataProperty.IsFullTextSearchable;

                    break;

                case VectorStoreRecordVectorProperty definitionVectorProperty:
                    if (property is not VectorStoreRecordVectorPropertyModel vectorProperty)
                    {
                        throw new InvalidOperationException($"Property '{property.ModelName}' is not a vector property.");
                    }

                    if (definitionVectorProperty.Dimensions is not null)
                    {
                        vectorProperty.Dimensions = definitionVectorProperty.Dimensions;
                    }

                    if (definitionVectorProperty.IndexKind is not null)
                    {
                        vectorProperty.IndexKind = definitionVectorProperty.IndexKind;
                    }

                    if (definitionVectorProperty.DistanceFunction is not null)
                    {
                        vectorProperty.DistanceFunction = definitionVectorProperty.DistanceFunction;
                    }

                    break;

                default:
                    throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.");
            }
        }
    }

    /// <summary>
    /// Extension hook for connectors to be able to customize the model.
    /// </summary>
    protected virtual void Customize()
    {
    }

    /// <summary>
    /// Finalizes the model after all properties have been processed, validating the model and applying some final transformations.
    /// </summary>
    protected virtual void Finalize(Type clrType)
    {
        if (!this.Options.UsesExternalSerializer && clrType.GetConstructor(Type.EmptyTypes) is null)
        {
            throw new NotSupportedException($"Type '{clrType.Name}' must have a parameterless constructor.");
        }

        if (!this.Options.SupportsMultipleKeys && this.KeyProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple key properties found on type '{clrType.Name}' or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (this.KeyProperties.Count == 0)
        {
            throw new NotSupportedException($"No key property found on type '{clrType.Name}' or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (this.Options.ReservedKeyStorageName is not null)
        {
            // Single key property validated in the constructor
            this.KeyProperties.Single().StorageName = this.Options.ReservedKeyStorageName;
        }

        if (this.Options.RequiresAtLeastOneVector && this.VectorProperties.Count == 0)
        {
            throw new NotSupportedException($"No vector property found on type '{clrType.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (!this.Options.SupportsMultipleVectors && this.VectorProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple vector properties found on type '{clrType.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        var storageNameMap = new Dictionary<string, VectorStoreRecordPropertyModel>();

        foreach (var property in this.PropertyMap.Values)
        {
            this.FinalizeProperty(property);

            if (storageNameMap.TryGetValue(property.StorageName, out var otherproperty))
            {
                throw new InvalidOperationException($"Property '{property.ModelName}' is being mapped to storage name '{property.StorageName}', but property '{otherproperty.ModelName}' is already mapped to the same storage name.");
            }

            storageNameMap[property.StorageName] = property;
        }
    }

    /// <summary>
    /// Finalizes a single property, performing validation on it.ssss
    /// </summary>
    protected virtual void FinalizeProperty(VectorStoreRecordPropertyModel propertyModel)
    {
        var clrType = propertyModel.ClrType;

        if (clrType.IsGenericType && clrType.GetGenericTypeDefinition() == typeof(Nullable<>))
        {
            clrType = clrType.GetGenericArguments()[0];
        }

        switch (propertyModel)
        {
            case VectorStoreRecordKeyPropertyModel keyProperty:
                if (this.Options.SupportedKeyPropertyTypes is not null)
                {
                    ValidatePropertyType(propertyModel.ModelName, clrType, "Key", this.Options.SupportedKeyPropertyTypes);
                }
                break;

            case VectorStoreRecordDataPropertyModel dataProperty:
                if (this.Options.SupportedDataPropertyTypes is not null)
                {
                    ValidatePropertyType(propertyModel.ModelName, clrType, "Data", this.Options.SupportedDataPropertyTypes, this.Options.SupportedEnumerableDataPropertyTypes);
                }
                break;

            case VectorStoreRecordVectorPropertyModel vectorProperty:
                if (this.Options.SupportedVectorPropertyTypes is not null)
                {
                    ValidatePropertyType(propertyModel.ModelName, clrType, "Vector", this.Options.SupportedVectorPropertyTypes);
                }
                break;

            default:
                throw new UnreachableException();
        }
    }

    private static void ValidatePropertyType(string propertyName, Type propertyType, string propertyCategoryDescription, HashSet<Type> supportedTypes, HashSet<Type>? supportedEnumerableElementTypes = null)
    {
        // Add shortcut before testing all the more expensive scenarios.
        if (supportedTypes.Contains(propertyType))
        {
            return;
        }

        // Check all collection scenarios and get stored type.
        if (supportedEnumerableElementTypes?.Count > 0 && IsSupportedEnumerableType(propertyType))
        {
            var typeToCheck = GetCollectionElementType(propertyType);

            if (!supportedEnumerableElementTypes.Contains(typeToCheck))
            {
                var supportedEnumerableElementTypesString = string.Join(", ", supportedEnumerableElementTypes!.Select(t => t.FullName));
                throw new NotSupportedException($"Enumerable {propertyCategoryDescription} properties must have one of the supported element types: {supportedEnumerableElementTypesString}. Element type of the property '{propertyName}' is {typeToCheck.FullName}.");
            }
        }
        else
        {
            // if we got here, we know the type is not supported
            var supportedTypesString = string.Join(", ", supportedTypes.Select(t => t.FullName));
            throw new NotSupportedException($"{propertyCategoryDescription} properties must be one of the supported types: {supportedTypesString}. Type of the property '{propertyName}' is {propertyType.FullName}.");
        }
    }

    private static bool IsSupportedEnumerableType(Type type)
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

    private static Type GetCollectionElementType(Type collectionType)
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
