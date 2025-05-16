﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a builder for a <see cref="CollectionModel"/>.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
/// <remarks>Note that this class is single-use only, and not thread-safe.</remarks>
[Experimental("MEVD9001")]
public abstract class CollectionModelBuilder
{
    /// <summary>
    /// Options for building the model.
    /// </summary>
    protected CollectionModelBuildingOptions Options { get; }

    /// <summary>
    /// The key properties of the record.
    /// </summary>
    protected List<KeyPropertyModel> KeyProperties { get; } = [];

    /// <summary>
    /// The data properties of the record.
    /// </summary>
    protected List<DataPropertyModel> DataProperties { get; } = [];

    /// <summary>
    /// The vector properties of the record.
    /// </summary>
    protected List<VectorPropertyModel> VectorProperties { get; } = [];

    /// <summary>
    /// All properties of the record, of all types.
    /// </summary>
    protected IEnumerable<PropertyModel> Properties => this.PropertyMap.Values;

    /// <summary>
    /// All properties of the record, of all types, indexed by their model name.
    /// </summary>
    protected Dictionary<string, PropertyModel> PropertyMap { get; } = new();

    /// <summary>
    /// The default embedding generator to use for vector properties, when none is specified at the property or collection level.
    /// </summary>
    protected IEmbeddingGenerator? DefaultEmbeddingGenerator { get; private set; }

    /// <summary>
    /// Constructs a new <see cref="CollectionModelBuilder"/>.
    /// </summary>
    protected CollectionModelBuilder(CollectionModelBuildingOptions options)
    {
        if (options.SupportsMultipleKeys && options.ReservedKeyStorageName is not null)
        {
            throw new ArgumentException($"{nameof(CollectionModelBuildingOptions.ReservedKeyStorageName)} cannot be set when {nameof(CollectionModelBuildingOptions.SupportsMultipleKeys)} is set.");
        }

        this.Options = options;
    }

    /// <summary>
    /// Builds and returns an <see cref="CollectionModel"/> from the given <paramref name="type"/> and <paramref name="definition"/>.
    /// </summary>
    [RequiresDynamicCode("This model building variant is not compatible with NativeAOT. See BuildDynamic() for dynamic mapping, and a third variant accepting source-generated delegates will be introduced in the future.")]
    [RequiresUnreferencedCode("This model building variant is not compatible with trimming. See BuildDynamic() for dynamic mapping, and a third variant accepting source-generated delegates will be introduced in the future.")]
    public virtual CollectionModel Build(Type type, VectorStoreRecordDefinition? definition, IEmbeddingGenerator? defaultEmbeddingGenerator)
    {
        if (type == typeof(Dictionary<string, object?>))
        {
            throw new ArgumentException("Dynamic mapping with Dictionary<string, object?> requires calling BuildDynamic().");
        }

        this.DefaultEmbeddingGenerator = defaultEmbeddingGenerator;

        this.ProcessTypeProperties(type, definition);

        if (definition is not null)
        {
            this.ProcessRecordDefinition(definition, type);
        }

        // Go over the properties, set the PropertyInfos to point to the .NET type's properties and validate type compatibility.
        foreach (var property in this.Properties)
        {
            // When we have a CLR type (POCO, not dynamic mapping), get the .NET property's type and make sure it matches the definition.
            property.PropertyInfo = type.GetProperty(property.ModelName)
                ?? throw new InvalidOperationException($"Property '{property.ModelName}' not found on CLR type '{type.FullName}'.");

            var clrPropertyType = property.PropertyInfo.PropertyType;
            if ((Nullable.GetUnderlyingType(clrPropertyType) ?? clrPropertyType) != (Nullable.GetUnderlyingType(property.Type) ?? property.Type))
            {
                throw new InvalidOperationException(
                    $"Property '{property.ModelName}' has a different CLR type in the record definition ('{property.Type.Name}') and on the .NET property ('{property.PropertyInfo.PropertyType}').");
            }
        }

        this.Customize();
        this.Validate(type);

        // Extra validation for non-dynamic mapping scenarios: ensure the type has a parameterless constructor.
        if (!this.Options.UsesExternalSerializer && type.GetConstructor(Type.EmptyTypes) is null)
        {
            throw new NotSupportedException($"Type '{type.Name}' must have a parameterless constructor.");
        }

        return new(type, new ActivatorBasedRecordCreator(), this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// Builds and returns an <see cref="CollectionModel"/> for dynamic mapping scenarios from the given <paramref name="definition"/>.
    /// </summary>
    public virtual CollectionModel BuildDynamic(VectorStoreRecordDefinition definition, IEmbeddingGenerator? defaultEmbeddingGenerator)
    {
        if (definition is null)
        {
            throw new ArgumentException("Vector store record definition must be provided for dynamic mapping.");
        }

        this.DefaultEmbeddingGenerator = defaultEmbeddingGenerator;
        this.ProcessRecordDefinition(definition, type: null);
        this.Customize();
        this.Validate(type: null);

        return new(typeof(Dictionary<string, object?>), new DynamicRecordCreator(), this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// As part of building the model, this method processes the properties of the given <paramref name="type"/>,
    /// detecting and reading attributes that affect the model. Not called for dynamic mapping scenarios.
    /// </summary>
    // TODO: This traverses the CLR type's properties, making it incompatible with trimming (and NativeAOT).
    // TODO: We could put [DynamicallyAccessedMembers] to preserve all properties, but that approach wouldn't
    // TODO: work with hierarchical data models (#10957).
    [RequiresUnreferencedCode("Traverses the CLR type's properties with reflection, so not compatible with trimming")]
    protected virtual void ProcessTypeProperties(Type type, VectorStoreRecordDefinition? definition)
    {
        // We want to allow the user-provided record definition to override anything configured via attributes
        // (allowing the same CLR type + attributes to be used with different record definitions).
        foreach (var clrProperty in type.GetProperties())
        {
            PropertyModel? property = null;
            string? storageName = null;

            if (clrProperty.GetCustomAttribute<VectorStoreKeyAttribute>() is { } keyAttribute)
            {
                var keyProperty = new KeyPropertyModel(clrProperty.Name, clrProperty.PropertyType);
                this.KeyProperties.Add(keyProperty);
                storageName = keyAttribute.StorageName;
                property = keyProperty;
            }

            if (clrProperty.GetCustomAttribute<VectorStoreDataAttribute>() is { } dataAttribute)
            {
                if (property is not null)
                {
                    // TODO: Test
                    throw new InvalidOperationException($"Property '{type.Name}.{clrProperty.Name}' has multiple of {nameof(VectorStoreKeyAttribute)}, {nameof(VectorStoreDataAttribute)} or {nameof(VectorStoreVectorAttribute)}. Only one of these attributes can be specified on a property.");
                }

                var dataProperty = new DataPropertyModel(clrProperty.Name, clrProperty.PropertyType)
                {
                    IsIndexed = dataAttribute.IsIndexed,
                    IsFullTextIndexed = dataAttribute.IsFullTextIndexed,
                };

                this.DataProperties.Add(dataProperty);
                storageName = dataAttribute.StorageName;
                property = dataProperty;
            }

            if (clrProperty.GetCustomAttribute<VectorStoreVectorAttribute>() is { } vectorAttribute)
            {
                if (property is not null)
                {
                    throw new InvalidOperationException($"Only one of {nameof(VectorStoreKeyAttribute)}, {nameof(VectorStoreDataAttribute)} and {nameof(VectorStoreVectorAttribute)} can be applied to a property.");
                }

                // If a record definition exists for the property, we must instantiate it via that definition, as the user may be using
                // a generic VectorStoreRecordVectorProperty<TInput> for a custom input type.
                var vectorProperty = definition?.Properties.FirstOrDefault(p => p.Name == clrProperty.Name) is VectorStoreVectorProperty definitionVectorProperty
                    ? definitionVectorProperty.CreatePropertyModel()
                    : new VectorPropertyModel(clrProperty.Name, clrProperty.PropertyType);

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

                if (this.DefaultEmbeddingGenerator is null || this.IsVectorPropertyTypeValid(clrProperty.PropertyType, out _))
                {
                    vectorProperty.EmbeddingType = clrProperty.PropertyType;
                }
                else
                {
                    this.SetupEmbeddingGeneration(vectorProperty, this.DefaultEmbeddingGenerator, embeddingType: null);
                }

                this.VectorProperties.Add(vectorProperty);
                storageName = vectorAttribute.StorageName;
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
    /// As part of building the model, this method processes the given <paramref name="definition"/>.
    /// </summary>
    protected virtual void ProcessRecordDefinition(VectorStoreRecordDefinition definition, Type? type)
    {
        foreach (VectorStoreProperty definitionProperty in definition.Properties)
        {
            if (!this.PropertyMap.TryGetValue(definitionProperty.Name, out var property))
            {
                // Property wasn't found attribute-annotated on the CLR type, so we need to add it.

                // TODO: Make the property CLR type optional - no need to specify it when using a CLR type.
                switch (definitionProperty)
                {
                    case VectorStoreKeyProperty definitionKeyProperty:
                        var keyProperty = new KeyPropertyModel(definitionKeyProperty.Name, definitionKeyProperty.Type);
                        this.KeyProperties.Add(keyProperty);
                        this.PropertyMap.Add(definitionKeyProperty.Name, keyProperty);
                        property = keyProperty;
                        break;
                    case VectorStoreDataProperty definitionDataProperty:
                        var dataProperty = new DataPropertyModel(definitionDataProperty.Name, definitionDataProperty.Type);
                        this.DataProperties.Add(dataProperty);
                        this.PropertyMap.Add(definitionDataProperty.Name, dataProperty);
                        property = dataProperty;
                        break;
                    case VectorStoreVectorProperty definitionVectorProperty:
                        var vectorProperty = definitionVectorProperty.CreatePropertyModel();
                        this.VectorProperties.Add(vectorProperty);
                        this.PropertyMap.Add(definitionVectorProperty.Name, vectorProperty);
                        property = vectorProperty;
                        break;
                    default:
                        throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.");
                }
            }

            property.Type = definitionProperty.Type;
            this.SetPropertyStorageName(property, definitionProperty.StorageName, type);

            switch (definitionProperty)
            {
                case VectorStoreKeyProperty definitionKeyProperty:
                    if (property is not KeyPropertyModel keyPropertyModel)
                    {
                        throw new InvalidOperationException(
                            $"Property '{property.ModelName}' is present in the {nameof(VectorStoreRecordDefinition)} as a key property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
                    }

                    break;

                case VectorStoreDataProperty definitionDataProperty:
                    if (property is not DataPropertyModel dataProperty)
                    {
                        throw new InvalidOperationException(
                            $"Property '{property.ModelName}' is present in the {nameof(VectorStoreRecordDefinition)} as a data property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
                    }

                    dataProperty.IsIndexed = definitionDataProperty.IsIndexed;
                    dataProperty.IsFullTextIndexed = definitionDataProperty.IsFullTextIndexed;

                    break;

                case VectorStoreVectorProperty definitionVectorProperty:
                    if (property is not VectorPropertyModel vectorProperty)
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
                        if (this.IsVectorPropertyTypeValid(vectorProperty.Type, out _))
                        {
                            throw new InvalidOperationException(VectorDataStrings.EmbeddingPropertyTypeIncompatibleWithEmbeddingGenerator(vectorProperty));
                        }

                        embeddingGenerator = definitionVectorProperty.EmbeddingGenerator;
                    }
                    // If a default embedding generator is defined (at the collection or store level), configure that on the property, but only if the property type is not an embedding type.
                    // If the property type is an embedding type, just ignore the default embedding generator.
                    else if ((definition.EmbeddingGenerator ?? this.DefaultEmbeddingGenerator) is IEmbeddingGenerator defaultEmbeddingGenerator
                        && !this.IsVectorPropertyTypeValid(vectorProperty.Type, out _))
                    {
                        embeddingGenerator = definition.EmbeddingGenerator ?? this.DefaultEmbeddingGenerator;
                    }

                    if (embeddingGenerator is null)
                    {
                        // No embedding generation - the embedding type and the property (model) type are the same.
                        vectorProperty.EmbeddingType = vectorProperty.Type;
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

    private void SetPropertyStorageName(PropertyModel property, string? storageName, Type? type)
    {
        if (property is KeyPropertyModel && this.Options.ReservedKeyStorageName is not null)
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
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? embeddingType)
    {
        if (!vectorProperty.TrySetupEmbeddingGeneration<Embedding<float>, ReadOnlyMemory<float>>(embeddingGenerator, embeddingType))
        {
            throw new InvalidOperationException(
                VectorDataStrings.IncompatibleEmbeddingGenerator(
                    embeddingGeneratorType: embeddingGenerator.GetType(),
                    supportedInputTypes: vectorProperty.GetSupportedInputTypes(),
                    supportedOutputTypes: [typeof(ReadOnlyMemory<float>)]));
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
    protected virtual void Validate(Type? type)
    {
        if (!this.Options.SupportsMultipleKeys && this.KeyProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple key properties found on {TypeMessage()}the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        if (this.KeyProperties.Count == 0)
        {
            throw new NotSupportedException($"No key property found on {TypeMessage()}the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (this.Options.RequiresAtLeastOneVector && this.VectorProperties.Count == 0)
        {
            throw new NotSupportedException($"No vector property found on {TypeMessage()}the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (!this.Options.SupportsMultipleVectors && this.VectorProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple vector properties found on {TypeMessage()}the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        var storageNameMap = new Dictionary<string, PropertyModel>();

        foreach (var property in this.PropertyMap.Values)
        {
            this.ValidateProperty(property);

            if (storageNameMap.TryGetValue(property.StorageName, out var otherproperty))
            {
                throw new InvalidOperationException($"Property '{property.ModelName}' is being mapped to storage name '{property.StorageName}', but property '{otherproperty.ModelName}' is already mapped to the same storage name.");
            }

            storageNameMap[property.StorageName] = property;
        }

        string TypeMessage() => type is null ? "" : $"type '{type.Name}' or ";
    }

    /// <summary>
    /// Validates a single property, performing validation on it.
    /// </summary>
    protected virtual void ValidateProperty(PropertyModel propertyModel)
    {
        var type = propertyModel.Type;

        Debug.Assert(propertyModel.Type is not null);

        switch (propertyModel)
        {
            case KeyPropertyModel keyProperty:
                if (!this.IsKeyPropertyTypeValid(keyProperty.Type, out var supportedTypes))
                {
                    throw new NotSupportedException(
                        $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: {supportedTypes}.");
                }
                break;

            case DataPropertyModel dataProperty:
                if (!this.IsDataPropertyTypeValid(dataProperty.Type, out supportedTypes))
                {
                    throw new NotSupportedException(
                        $"Property '{dataProperty.ModelName}' has unsupported type '{type.Name}'. Data properties must be one of the supported types: {supportedTypes}.");
                }
                break;

            case VectorPropertyModel vectorProperty:
                Debug.Assert(vectorProperty.EmbeddingGenerator is null ^ vectorProperty.Type != vectorProperty.EmbeddingType);

                if (!this.IsVectorPropertyTypeValid(vectorProperty.EmbeddingType, out supportedTypes))
                {
                    throw new InvalidOperationException(
                        vectorProperty.EmbeddingGenerator is null
                            ? VectorDataStrings.NonEmbeddingVectorPropertyWithoutEmbeddingGenerator(vectorProperty)
                            : VectorDataStrings.EmbeddingPropertyTypeIncompatibleWithEmbeddingGenerator(vectorProperty));
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

    /// <summary>
    /// Validates that the .NET type for a key property is supported by the provider.
    /// </summary>
    protected abstract bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes);

    /// <summary>
    /// Validates that the .NET type for a data property is supported by the provider.
    /// </summary>
    protected abstract bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes);

    /// <summary>
    /// Validates that the .NET type for a vector property is supported by the provider.
    /// </summary>
    protected abstract bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes);

    [RequiresUnreferencedCode("This record creator is incompatible with trimming and is only used in non-trimming compatible codepaths")]
    private sealed class ActivatorBasedRecordCreator : IRecordCreator
    {
        public TRecord Create<TRecord>()
            => Activator.CreateInstance<TRecord>() ?? throw new InvalidOperationException($"Failed to instantiate record of type '{typeof(TRecord).Name}'.");
    }

    private sealed class DynamicRecordCreator : IRecordCreator
    {
        public TRecord Create<TRecord>()
            => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? (TRecord)(object)new Dictionary<string, object?>()
                : throw new UnreachableException($"Dynamic record creator only supports Dictionary<string, object?>, but got {typeof(TRecord).Name}.");
    }
}
