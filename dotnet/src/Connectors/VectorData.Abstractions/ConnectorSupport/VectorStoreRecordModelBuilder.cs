// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.Properties;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a builder for a <see cref="VectorStoreRecordModel"/>.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
/// <remarks>Note that this class is single-use only, and not thread-safe.</remarks>
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
    /// The default embedding generator to use for vector properties, when none is specified at the property or collection level.
    /// </summary>
    protected IEmbeddingGenerator? DefaultEmbeddingGenerator { get; private set; }

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
    /// Builds and returns an <see cref="VectorStoreRecordModel"/> from the given <paramref name="type"/> and <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    [RequiresDynamicCode("Currently not compatible with NativeAOT code")]
    [RequiresUnreferencedCode("Currently not compatible with trimming")] // TODO
    public virtual VectorStoreRecordModel Build(Type type, VectorStoreRecordDefinition? vectorStoreRecordDefinition, IEmbeddingGenerator? defaultEmbeddingGenerator)
    {
        this.DefaultEmbeddingGenerator = defaultEmbeddingGenerator;

        var dynamicMapping = type == typeof(Dictionary<string, object?>);

        if (!dynamicMapping)
        {
            this.ProcessTypeProperties(type, vectorStoreRecordDefinition);
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
            this.ProcessRecordDefinition(vectorStoreRecordDefinition, dynamicMapping ? null : type);
        }

        this.Customize();
        this.Validate(type);

        return new(type, this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// As part of building the model, this method processes the properties of the given <paramref name="type"/>,
    /// detecting and reading attributes that affect the model. Not called for dynamic mapping scenarios.
    /// </summary>
    // TODO: This traverses the CLR type's properties, making it incompatible with trimming (and NativeAOT).
    // TODO: We could put [DynamicallyAccessedMembers] to preserve all properties, but that approach wouldn't
    // TODO: work with hierarchical data models (#10957).
    [RequiresUnreferencedCode("Traverses the CLR type's properties with reflection, so not compatible with trimming")]
    protected virtual void ProcessTypeProperties(Type type, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        // We want to allow the user-provided record definition to override anything configured via attributes
        // (allowing the same CLR type + attributes to be used with different record definitions).
        foreach (var clrProperty in type.GetProperties())
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
                    throw new InvalidOperationException($"Property '{type.Name}.{clrProperty.Name}' has multiple of {nameof(VectorStoreRecordKeyAttribute)}, {nameof(VectorStoreRecordDataAttribute)} or {nameof(VectorStoreRecordVectorAttribute)}. Only one of these attributes can be specified on a property.");
                }

                var dataProperty = new VectorStoreRecordDataPropertyModel(clrProperty.Name, clrProperty.PropertyType)
                {
                    IsIndexed = dataAttribute.IsIndexed,
                    IsFullTextIndexed = dataAttribute.IsFullTextIndexed,
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

                // If a record definition exists for the property, we must instantiate it via that definition, as the user may be using
                // a generic VectorStoreRecordVectorProperty<TInput> for a custom input type.
                var vectorProperty = vectorStoreRecordDefinition?.Properties.FirstOrDefault(p => p.DataModelPropertyName == clrProperty.Name) is VectorStoreRecordVectorProperty definitionVectorProperty
                    ? definitionVectorProperty.CreatePropertyModel()
                    : new VectorStoreRecordVectorPropertyModel(clrProperty.Name, clrProperty.PropertyType);

                vectorProperty.Dimensions = vectorAttribute.Dimensions;
                vectorProperty.IndexKind = vectorAttribute.IndexKind;
                vectorProperty.DistanceFunction = vectorAttribute.DistanceFunction;

                // If a default embedding generator is defined and the property type isn't an Embedding, we set up that embedding generator on the property.
                // At this point we don't know the embedding type (it might get specified in the record definition, that's processed later). So we infer
                //
                // This also means that the property type is the input type (e.g. string, DataContent) rather than the embedding type.
                // Since we need the property type to be the embedding type, we infer that from the generator. This allows users
                // to just stick an IEmbeddingGenerator in DI, define a string property as their vector property, and as long as the embedding generator
                // is compatible (supports string and ROM<float>, assuming that's what the connector requires), everything just works.
                // Note that inferring the embedding type from the IEmbeddingGenerator isn't trivial, involving both connector logic (around which embedding
                // types are supported/preferred), as well as the vector property type (which knows about supported input types).

                if (this.DefaultEmbeddingGenerator is null || this.Options.SupportedVectorPropertyTypes.Contains(clrProperty.PropertyType))
                {
                    vectorProperty.EmbeddingType = clrProperty.PropertyType;
                }
                else
                {
                    this.SetupEmbeddingGeneration(vectorProperty, this.DefaultEmbeddingGenerator, embeddingType: null);
                }

                this.VectorProperties.Add(vectorProperty);
                storageName = vectorAttribute.StoragePropertyName;
                property = vectorProperty;
            }

            if (property is null)
            {
                // No mapping attribute was found, ignore this property.
                continue;
            }

            this.SetPropertyStorageName(property, storageName, type);

            property.PropertyInfo = clrProperty;
            this.PropertyMap.Add(clrProperty.Name, property);
        }
    }

    /// <summary>
    /// As part of building the model, this method processes the given <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    protected virtual void ProcessRecordDefinition(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type? type)
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
                        var vectorProperty = definitionVectorProperty.CreatePropertyModel();
                        this.VectorProperties.Add(vectorProperty);
                        this.PropertyMap.Add(definitionVectorProperty.DataModelPropertyName, vectorProperty);
                        property = vectorProperty;
                        break;
                    default:
                        throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.");
                }

                if (type is not null)
                {
                    // If we have a CLR type (POCO, not dynamic mapping), get the .NET property's type and make sure it matches the definition.
                    property.PropertyInfo = type.GetProperty(property.ModelName)
                        ?? throw new InvalidOperationException($"Property '{property.ModelName}' not found on CLR type '{type.FullName}'.");

                    if (property.PropertyInfo.PropertyType != property.Type)
                    {
                        throw new InvalidOperationException($"Property '{property.ModelName}' has a different CLR type in the record definition ('{property.Type.Name}') and on the .NET property ('{property.PropertyInfo.PropertyType}').");
                    }
                }
            }

            property.Type = definitionProperty.PropertyType;
            this.SetPropertyStorageName(property, definitionProperty.StoragePropertyName, type);

            switch (definitionProperty)
            {
                case VectorStoreRecordKeyProperty definitionKeyProperty:
                    if (property is not VectorStoreRecordKeyPropertyModel keyPropertyModel)
                    {
                        throw new InvalidOperationException(
                            $"Property '{property.ModelName}' is present in the {nameof(VectorStoreRecordDefinition)} as a key property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
                    }

                    break;

                case VectorStoreRecordDataProperty definitionDataProperty:
                    if (property is not VectorStoreRecordDataPropertyModel dataProperty)
                    {
                        throw new InvalidOperationException(
                            $"Property '{property.ModelName}' is present in the {nameof(VectorStoreRecordDefinition)} as a data property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
                    }

                    dataProperty.IsIndexed = definitionDataProperty.IsIndexed;
                    dataProperty.IsFullTextIndexed = definitionDataProperty.IsFullTextIndexed;

                    break;

                case VectorStoreRecordVectorProperty definitionVectorProperty:
                    if (property is not VectorStoreRecordVectorPropertyModel vectorProperty)
                    {
                        throw new InvalidOperationException(
                            $"Property '{property.ModelName}' is present in the {nameof(VectorStoreRecordDefinition)} as a vector property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
                    }

                    vectorProperty.Dimensions = definitionVectorProperty.Dimensions;

                    if (definitionVectorProperty.IndexKind is not null)
                    {
                        vectorProperty.IndexKind = definitionVectorProperty.IndexKind;
                    }

                    if (definitionVectorProperty.DistanceFunction is not null)
                    {
                        vectorProperty.DistanceFunction = definitionVectorProperty.DistanceFunction;
                    }

                    if (definitionVectorProperty.EmbeddingType is not null)
                    {
                        vectorProperty.EmbeddingType = definitionVectorProperty.EmbeddingType;
                    }

                    // Check if embedding generation is configured, either on the property directly or via a default
                    IEmbeddingGenerator? embeddingGenerator = null;

                    // Check if an embedding generator is defined specifically on the property.
                    if (definitionVectorProperty.EmbeddingGenerator is not null)
                    {
                        // If we have a property CLR type (POCO, not dynamic mapping) and it's an embedding type, throw as that's incompatible.
                        if (this.Options.SupportedVectorPropertyTypes.Contains(property.Type))
                        {
                            throw new InvalidOperationException(
                                string.Format(
                                    VectorDataStrings.EmbeddingPropertyTypeIncompatibleWithEmbeddingGenerator,
                                    property.ModelName,
                                    property.Type.Name));
                        }

                        embeddingGenerator = definitionVectorProperty.EmbeddingGenerator;
                    }
                    // If a default embedding generator is defined (at the collection or store level), configure that on the property, but only if the property type is not an embedding type.
                    // If the property type is an embedding type, just ignore the default embedding generator.
                    else if ((vectorStoreRecordDefinition.EmbeddingGenerator ?? this.DefaultEmbeddingGenerator) is IEmbeddingGenerator defaultEmbeddingGenerator
                        && !this.Options.SupportedVectorPropertyTypes.Contains(property.Type))
                    {
                        embeddingGenerator = vectorStoreRecordDefinition.EmbeddingGenerator ?? this.DefaultEmbeddingGenerator;
                    }

                    if (embeddingGenerator is null)
                    {
                        // No embedding generation - the embedding type and the property (model) type are the same.
                        vectorProperty.EmbeddingType = property.Type;
                    }
                    else
                    {
                        this.SetupEmbeddingGeneration(vectorProperty, embeddingGenerator, vectorProperty.EmbeddingType);
                    }
                    break;

                default:
                    throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.");
            }
        }
    }

    private void SetPropertyStorageName(VectorStoreRecordPropertyModel property, string? storageName, Type? type)
    {
        if (property is VectorStoreRecordKeyPropertyModel && this.Options.ReservedKeyStorageName is not null)
        {
            // If we have ReservedKeyStorageName, there can only be a single key property (validated in the constructor)
            property.StorageName = this.Options.ReservedKeyStorageName;
            return;
        }

        if (storageName is null)
        {
            return;
        }

        // If a custom serializer is used (e.g. JsonSerializer), it would ignore our own attributes/config, and
        // our model needs to be in sync with the serializer's behavior (for e.g. storage names in filters).
        // So we ignore the config here as well.
        // TODO: Consider throwing here instead of ignoring
        if (this.Options.UsesExternalSerializer && type != null)
        {
            return;
        }

        property.StorageName = this.Options.EscapeIdentifier is not null
            ? this.Options.EscapeIdentifier(storageName)
            : storageName;
    }

    /// <summary>
    /// Attempts to setup embedding generation on the given vector property, with the given embedding generator and user-configured embedding type.
    /// Can be overridden by connectors to provide support for other embedding types.
    /// </summary>
    protected virtual void SetupEmbeddingGeneration(
        VectorStoreRecordVectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? embeddingType)
    {
        if (!vectorProperty.TrySetupEmbeddingGeneration<Embedding<float>, ReadOnlyMemory<float>>(embeddingGenerator, embeddingType))
        {
            throw new InvalidOperationException(
                string.Format(
                    VectorDataStrings.IncompatibleEmbeddingGenerator,
                    embeddingGenerator.GetType().Name,
                    string.Join(", ", vectorProperty.GetSupportedInputTypes().Select(t => t.Name)),
                    "ReadOnlyMemory<float>"));
        }
    }

    /// <summary>
    /// Extension hook for connectors to be able to customize the model.
    /// </summary>
    protected virtual void Customize()
    {
    }

    /// <summary>
    /// Validates the model after all properties have been processed.
    /// </summary>
    protected virtual void Validate(Type type)
    {
        if (!this.Options.UsesExternalSerializer && type.GetConstructor(Type.EmptyTypes) is null)
        {
            throw new NotSupportedException($"Type '{type.Name}' must have a parameterless constructor.");
        }

        if (!this.Options.SupportsMultipleKeys && this.KeyProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple key properties found on type '{type.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        if (this.KeyProperties.Count == 0)
        {
            throw new NotSupportedException($"No key property found on type '{type.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (this.Options.RequiresAtLeastOneVector && this.VectorProperties.Count == 0)
        {
            throw new NotSupportedException($"No vector property found on type '{type.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (!this.Options.SupportsMultipleVectors && this.VectorProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple vector properties found on type '{type.Name}' or the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        var storageNameMap = new Dictionary<string, VectorStoreRecordPropertyModel>();

        foreach (var property in this.PropertyMap.Values)
        {
            this.ValidateProperty(property);

            if (storageNameMap.TryGetValue(property.StorageName, out var otherproperty))
            {
                throw new InvalidOperationException($"Property '{property.ModelName}' is being mapped to storage name '{property.StorageName}', but property '{otherproperty.ModelName}' is already mapped to the same storage name.");
            }

            storageNameMap[property.StorageName] = property;
        }
    }

    /// <summary>
    /// Validates a single property, performing validation on it.
    /// </summary>
    protected virtual void ValidateProperty(VectorStoreRecordPropertyModel propertyModel)
    {
        var type = propertyModel.Type;

        Debug.Assert(propertyModel.Type is not null);

        if (type.IsGenericType && Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        switch (propertyModel)
        {
            case VectorStoreRecordKeyPropertyModel keyProperty:
                if (this.Options.SupportedKeyPropertyTypes is not null)
                {
                    ValidatePropertyType(propertyModel.ModelName, type, "Key", this.Options.SupportedKeyPropertyTypes);
                }
                break;

            case VectorStoreRecordDataPropertyModel dataProperty:
                if (this.Options.SupportedDataPropertyTypes is not null)
                {
                    ValidatePropertyType(propertyModel.ModelName, type, "Data", this.Options.SupportedDataPropertyTypes, this.Options.SupportedEnumerableDataPropertyElementTypes);
                }
                break;

            case VectorStoreRecordVectorPropertyModel vectorProperty:
                Debug.Assert(vectorProperty.EmbeddingGenerator is null ^ vectorProperty.Type != vectorProperty.EmbeddingType);

                if (!this.Options.SupportedVectorPropertyTypes.Contains(vectorProperty.EmbeddingType))
                {
                    throw new InvalidOperationException(
                        vectorProperty.EmbeddingGenerator is null
                            ? string.Format(VectorDataStrings.NonEmbeddingVectorPropertyWithoutEmbeddingGenerator, vectorProperty.ModelName, vectorProperty.EmbeddingType.Name)
                            : string.Format(VectorDataStrings.EmbeddingGeneratorWithInvalidEmbeddingType, vectorProperty.ModelName, vectorProperty.EmbeddingType.Name));
                }

                if (vectorProperty.Dimensions <= 0)
                {
                    throw new InvalidOperationException($"Vector property '{propertyModel.ModelName}' must have a positive number of dimensions.");
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
            var supportedEnumerableTypesString = supportedEnumerableElementTypes is { Count: > 0 } ? string.Join(", ", supportedEnumerableElementTypes.Select(t => t.FullName)) : null;
            throw new NotSupportedException($"""
                Property '{propertyName}' has unsupported type '{propertyType.Name}'.
                {propertyCategoryDescription} properties must be one of the supported types: {supportedTypesString}{(supportedEnumerableElementTypes is null ? "" : ", or a collection type over: " + supportedEnumerableElementTypes)}.
                """);
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
