// Copyright (c) Microsoft. All rights reserved.

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
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
/// <remarks>This class is single-use only, and not thread-safe.</remarks>
[Experimental("MEVD9001")]
public abstract class CollectionModelBuilder
{
    /// <summary>
    /// Gets the options for building the model.
    /// </summary>
    protected CollectionModelBuildingOptions Options { get; }

    /// <summary>
    /// Gets the key properties of the record.
    /// </summary>
    protected List<KeyPropertyModel> KeyProperties { get; } = [];

    /// <summary>
    /// Gets the data properties of the record.
    /// </summary>
    protected List<DataPropertyModel> DataProperties { get; } = [];

    /// <summary>
    /// Gets the vector properties of the record.
    /// </summary>
    protected List<VectorPropertyModel> VectorProperties { get; } = [];

    /// <summary>
    /// Gets all properties of the record, of all types.
    /// </summary>
    protected IEnumerable<PropertyModel> Properties => this.PropertyMap.Values;

    /// <summary>
    /// Gets all properties of the record, of all types, indexed by their model name.
    /// </summary>
    protected Dictionary<string, PropertyModel> PropertyMap { get; } = [];

    /// <summary>
    /// Gets the default embedding generator to use for vector properties, when none is specified at the property or collection level.
    /// </summary>
    protected IEmbeddingGenerator? DefaultEmbeddingGenerator { get; private set; }

    /// <summary>
    /// Gets the collection's generic key type parameter (<c>TKey</c>), if provided.
    /// Used by <see cref="ValidateKeyProperty"/> to validate that <c>TKey</c> corresponds to the key property type on the model.
    /// </summary>
    protected Type? KeyType { get; private set; }

    /// <summary>
    /// Constructs a new <see cref="CollectionModelBuilder"/>.
    /// </summary>
    protected CollectionModelBuilder(CollectionModelBuildingOptions options)
        => this.Options = options;

    /// <summary>
    /// Builds and returns an <see cref="CollectionModel"/> from the given <paramref name="recordType"/> and <paramref name="definition"/>.
    /// </summary>
    /// <param name="recordType">The CLR type of the record.</param>
    /// <param name="keyType">The collection's generic key type parameter (<c>TKey</c>), used to validate correspondence with the key property type.</param>
    /// <param name="definition">An optional record definition that overrides attribute-based configuration.</param>
    /// <param name="defaultEmbeddingGenerator">An optional default embedding generator for vector properties.</param>
    [RequiresDynamicCode("This model building variant is not compatible with NativeAOT. See BuildDynamic() for dynamic mapping, and a third variant accepting source-generated delegates will be introduced in the future.")]
    [RequiresUnreferencedCode("This model building variant is not compatible with trimming. See BuildDynamic() for dynamic mapping, and a third variant accepting source-generated delegates will be introduced in the future.")]
    public virtual CollectionModel Build(Type recordType, Type keyType, VectorStoreCollectionDefinition? definition, IEmbeddingGenerator? defaultEmbeddingGenerator)
    {
        this.KeyType = keyType;

        if (recordType == typeof(Dictionary<string, object?>))
        {
            throw new ArgumentException("Dynamic mapping with Dictionary<string, object?> requires calling BuildDynamic().");
        }

        this.DefaultEmbeddingGenerator = definition?.EmbeddingGenerator ?? defaultEmbeddingGenerator;

        // Build a lookup of definition properties by name for matching with CLR properties.
        Dictionary<string, VectorStoreProperty>? definitionByName = null;
        if (definition is not null)
        {
            definitionByName = [];
            foreach (var p in definition.Properties)
            {
                definitionByName[p.Name] = p;
            }
        }

        // Process CLR properties, matching to definition properties where available.
        // TODO: This traverses the CLR type's properties, making it incompatible with trimming (and NativeAOT).
        // TODO: We could put [DynamicallyAccessedMembers] to preserve all properties, but that approach wouldn't
        // TODO: work with hierarchical data models (#10957).
        foreach (var clrProperty in recordType.GetProperties())
        {
            VectorStoreProperty? definitionProperty = null;
            _ = definitionByName?.TryGetValue(clrProperty.Name, out definitionProperty);

            this.ProcessProperty(clrProperty, definitionProperty, recordType);
        }

        // Go over the properties, configure POCO accessors and validate type compatibility.
        foreach (var property in this.Properties)
        {
            var clrProperty = recordType.GetProperty(property.ModelName)
                ?? throw new InvalidOperationException($"Property '{property.ModelName}' not found on CLR type '{recordType.FullName}'.");

            var clrPropertyType = clrProperty.PropertyType;
            if ((Nullable.GetUnderlyingType(clrPropertyType) ?? clrPropertyType) != (Nullable.GetUnderlyingType(property.Type) ?? property.Type))
            {
                throw new InvalidOperationException(
                    $"Property '{property.ModelName}' has a different CLR type in the record definition ('{property.Type.Name}') and on the .NET property ('{clrProperty.PropertyType}').");
            }

            property.ConfigurePocoAccessors(clrProperty);
        }

        this.Customize();
        this.Validate(recordType, definition);

        // Extra validation for non-dynamic mapping scenarios: ensure the type has a parameterless constructor.
        if (!this.Options.UsesExternalSerializer && recordType.GetConstructor(Type.EmptyTypes) is null)
        {
            throw new NotSupportedException($"Type '{recordType.Name}' must have a parameterless constructor.");
        }

        return new(recordType, () => Activator.CreateInstance(recordType)!, this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// Builds and returns an <see cref="CollectionModel"/> for dynamic mapping scenarios from the given <paramref name="definition"/>.
    /// </summary>
    /// <param name="definition">The record definition describing the collection's schema.</param>
    /// <param name="defaultEmbeddingGenerator">An optional default embedding generator for vector properties.</param>
    public virtual CollectionModel BuildDynamic(VectorStoreCollectionDefinition definition, IEmbeddingGenerator? defaultEmbeddingGenerator)
    {
        if (definition is null)
        {
            throw new ArgumentException("Vector store record definition must be provided for dynamic mapping.");
        }

        this.DefaultEmbeddingGenerator = defaultEmbeddingGenerator;

        foreach (var defProp in definition.Properties)
        {
            this.ProcessProperty(clrProperty: null, defProp, type: null);
        }

        this.Customize();
        this.Validate(type: null, definition);

        foreach (var property in this.Properties)
        {
            property.ConfigureDynamicAccessors();
        }

        return new(typeof(Dictionary<string, object?>), static () => new Dictionary<string, object?>(), this.KeyProperties, this.DataProperties, this.VectorProperties, this.PropertyMap);
    }

    /// <summary>
    /// As part of building the model, this method processes a single property, accepting both a CLR <see cref="PropertyInfo"/>
    /// (from which attributes are read) and a <see cref="VectorStoreProperty"/> from the user-provided record definition.
    /// Either may be <see langword="null"/>, but not both.
    /// When both are provided, the record definition values override attribute-configured values.
    /// </summary>
    protected virtual void ProcessProperty(PropertyInfo? clrProperty, VectorStoreProperty? definitionProperty, Type? type)
    {
        Debug.Assert(clrProperty is not null || definitionProperty is not null);

        VectorStoreKeyAttribute? keyAttribute = null;
        VectorStoreDataAttribute? dataAttribute = null;
        VectorStoreVectorAttribute? vectorAttribute = null;

        if (clrProperty is not null)
        {
            // Read attributes from CLR property.
            keyAttribute = clrProperty.GetCustomAttribute<VectorStoreKeyAttribute>();
            dataAttribute = clrProperty.GetCustomAttribute<VectorStoreDataAttribute>();
            vectorAttribute = clrProperty.GetCustomAttribute<VectorStoreVectorAttribute>();

            // Validate that at most one mapping attribute is present.
            if ((keyAttribute is not null ? 1 : 0) + (dataAttribute is not null ? 1 : 0) + (vectorAttribute is not null ? 1 : 0) > 1)
            {
                throw new InvalidOperationException(
                    $"Property '{type!.Name}.{clrProperty.Name}' has multiple of {nameof(VectorStoreKeyAttribute)}, {nameof(VectorStoreDataAttribute)} or {nameof(VectorStoreVectorAttribute)}. Only one of these attributes can be specified on a property.");
            }

            // If no mapping attribute and no definition, skip this property.
            if (keyAttribute is null && dataAttribute is null && vectorAttribute is null && definitionProperty is null)
            {
                return;
            }

            // Validate kind compatibility between attribute and definition.
            if (definitionProperty is not null
                && ((keyAttribute is not null && definitionProperty is not VectorStoreKeyProperty)
                    || (dataAttribute is not null && definitionProperty is not VectorStoreDataProperty)
                    || (vectorAttribute is not null && definitionProperty is not VectorStoreVectorProperty)))
            {
                string definitionKind = definitionProperty switch
                {
                    VectorStoreKeyProperty => "key",
                    VectorStoreDataProperty => "data",
                    VectorStoreVectorProperty => "vector",
                    _ => throw new ArgumentException($"Unknown type '{definitionProperty.GetType().FullName}' in vector store record definition.")
                };

                throw new InvalidOperationException(
                    $"Property '{clrProperty.Name}' is present in the {nameof(VectorStoreCollectionDefinition)} as a {definitionKind} property, but the .NET property on type '{type?.Name}' has an incompatible attribute.");
            }
        }

        string propertyName = clrProperty?.Name ?? definitionProperty!.Name;
        Type propertyType = clrProperty?.PropertyType
            ?? definitionProperty!.Type
            ?? throw new InvalidOperationException(VectorDataStrings.MissingTypeOnPropertyDefinition(definitionProperty!));

        PropertyModel property;
        string? attributeStorageName = null;

        if (keyAttribute is not null || definitionProperty is VectorStoreKeyProperty)
        {
            var keyProperty = new KeyPropertyModel(propertyName, propertyType);

            if (keyAttribute is not null)
            {
                keyProperty.IsAutoGenerated = keyAttribute.IsAutoGeneratedNullable ?? this.SupportsKeyAutoGeneration(keyProperty.Type);
                attributeStorageName = keyAttribute.StorageName;
            }

            // Definition values override attribute values.
            if (definitionProperty is VectorStoreKeyProperty defKey)
            {
                keyProperty.IsAutoGenerated = defKey.IsAutoGenerated ?? this.SupportsKeyAutoGeneration(keyProperty.Type);
            }

            this.KeyProperties.Add(keyProperty);
            property = keyProperty;
        }
        else if (dataAttribute is not null || definitionProperty is VectorStoreDataProperty)
        {
            var dataProperty = new DataPropertyModel(propertyName, propertyType);

            if (dataAttribute is not null)
            {
                dataProperty.IsIndexed = dataAttribute.IsIndexed;
                dataProperty.IsFullTextIndexed = dataAttribute.IsFullTextIndexed;
                attributeStorageName = dataAttribute.StorageName;
            }

            // Definition values override attribute values.
            if (definitionProperty is VectorStoreDataProperty defData)
            {
                dataProperty.IsIndexed = defData.IsIndexed;
                dataProperty.IsFullTextIndexed = defData.IsFullTextIndexed;
            }

            this.DataProperties.Add(dataProperty);
            property = dataProperty;
        }
        else if (vectorAttribute is not null || definitionProperty is VectorStoreVectorProperty)
        {
            // If a definition exists, create via the definition to preserve generic type info (VectorStoreVectorProperty<TInput>).
            var vectorProperty = definitionProperty is VectorStoreVectorProperty defVec
                ? defVec.CreatePropertyModel()
                : new VectorPropertyModel(propertyName, propertyType);

            if (vectorAttribute is not null)
            {
                vectorProperty.Dimensions = vectorAttribute.Dimensions;
                vectorProperty.IndexKind = vectorAttribute.IndexKind;
                vectorProperty.DistanceFunction = vectorAttribute.DistanceFunction;
                attributeStorageName = vectorAttribute.StorageName;
            }

            // Definition values override attribute values.
            if (definitionProperty is VectorStoreVectorProperty defVectorProp)
            {
                vectorProperty.Dimensions = defVectorProp.Dimensions;

                if (defVectorProp.IndexKind is not null)
                {
                    vectorProperty.IndexKind = defVectorProp.IndexKind;
                }

                if (defVectorProp.DistanceFunction is not null)
                {
                    vectorProperty.DistanceFunction = defVectorProp.DistanceFunction;
                }
            }

            this.ConfigureVectorPropertyEmbedding(
                vectorProperty,
                (definitionProperty as VectorStoreVectorProperty)?.EmbeddingGenerator ?? this.DefaultEmbeddingGenerator,
                (definitionProperty as VectorStoreVectorProperty)?.EmbeddingType);

            this.VectorProperties.Add(vectorProperty);
            property = vectorProperty;
        }
        else
        {
            throw new UnreachableException();
        }

        // Apply storage name: attribute first, then definition (which takes precedence).
        this.SetPropertyStorageName(property, attributeStorageName, type);
        if (definitionProperty is not null)
        {
            this.SetPropertyStorageName(property, definitionProperty.StorageName, type);
        }

        if (definitionProperty?.ProviderAnnotations is not null)
        {
            property.ProviderAnnotations = new Dictionary<string, object?>(definitionProperty.ProviderAnnotations);
        }

        if (clrProperty is not null)
        {
            property.PropertyInfo = clrProperty;
        }

        this.PropertyMap.Add(propertyName, property);
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

        property.StorageName = storageName;
    }

    /// <summary>
    /// Gets the embedding types supported by this provider, in priority order.
    /// The first type whose embedding generator is compatible with the input type will be used.
    /// </summary>
    /// <remarks>
    /// Override this property in connectors that support additional embedding types beyond <see cref="Embedding{T}"/> of <see langword="float"/>.
    /// </remarks>
    protected virtual IReadOnlyList<EmbeddingGenerationDispatcher> EmbeddingGenerationDispatchers { get; }
        = [EmbeddingGenerationDispatcher.Create<Embedding<float>>()];

    /// <summary>
    /// Attempts to resolve the embedding type for the given vector property, iterating over <see cref="EmbeddingGenerationDispatchers"/> in priority order.
    /// </summary>
    private (Type? EmbeddingType, EmbeddingGenerationDispatcher? Handler) ResolveEmbeddingType(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? userRequestedEmbeddingType)
    {
        foreach (var supported in this.EmbeddingGenerationDispatchers)
        {
            if (supported.ResolveEmbeddingType(vectorProperty, embeddingGenerator, userRequestedEmbeddingType) is { } resolved)
            {
                return (resolved, supported);
            }
        }

        return (null, null);
    }

    /// <summary>
    /// Resolves the embedding handler for a native vector property type, where embedding generation is only needed for search.
    /// Since the property type is already a valid native type, we only check if the generator can produce the
    /// embedding output type (regardless of input type, which is only known at search time).
    /// </summary>
    private EmbeddingGenerationDispatcher? ResolveSearchOnlyEmbeddingHandler(VectorPropertyModel vectorProperty, IEmbeddingGenerator embeddingGenerator)
    {
        foreach (var supported in this.EmbeddingGenerationDispatchers)
        {
            if (supported.CanGenerateEmbedding(vectorProperty, embeddingGenerator))
            {
                return supported;
            }
        }

        return null;
    }

    /// <summary>
    /// Configures embedding generation for a vector property. Sets the embedding generator, resolves the embedding type,
    /// and assigns the appropriate <see cref="EmbeddingGenerationDispatcher"/>.
    /// </summary>
    /// <remarks>
    /// If the property's type is natively supported (e.g. <see cref="ReadOnlyMemory{T}"/> of <see langword="float"/>), the embedding type
    /// is set to the property's type; if a generator is also configured, a search-only dispatcher is resolved so that search can convert
    /// arbitrary inputs (e.g. string) to embeddings.
    /// Otherwise, if a generator is configured, the embedding type is resolved from it. If resolution fails, the embedding type remains
    /// <see langword="null"/> and an error is deferred to the validation phase.
    /// </remarks>
    private void ConfigureVectorPropertyEmbedding(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator? embeddingGenerator,
        Type? userRequestedEmbeddingType)
    {
        vectorProperty.EmbeddingGenerator = embeddingGenerator;

        if (this.IsVectorPropertyTypeValid(vectorProperty.Type, out _))
        {
            if (userRequestedEmbeddingType is not null && userRequestedEmbeddingType != vectorProperty.Type)
            {
                throw new InvalidOperationException(VectorDataStrings.DifferentEmbeddingTypeSpecifiedForNativelySupportedType(vectorProperty, userRequestedEmbeddingType));
            }

            vectorProperty.EmbeddingType = vectorProperty.Type;

            // Even for native types, if an embedding generator is configured, resolve the dispatcher
            // so that search can convert arbitrary inputs (e.g. string) to embeddings.
            if (embeddingGenerator is not null)
            {
                vectorProperty.EmbeddingGenerationDispatcher = this.ResolveSearchOnlyEmbeddingHandler(vectorProperty, embeddingGenerator);
            }
        }
        else if (embeddingGenerator is not null)
        {
            // The property type isn't a valid embedding type, but an embedding generator is configured.
            // Try to resolve the embedding type from it: if the configured generator supports translating the input type (e.g. string) to
            // an output type supported by the provider, we set that as the embedding type.
            // If this fails, EmbeddingType remains null and we defer the error to the validation phase.
            var (embeddingType, handler) = this.ResolveEmbeddingType(vectorProperty, embeddingGenerator, userRequestedEmbeddingType);
            vectorProperty.EmbeddingType = embeddingType;
            vectorProperty.EmbeddingGenerationDispatcher = handler;
        }

        // If the property type isn't valid and there's no embedding generator, that's an error.
        // But we throw later, in validation, to allow for provider customization to correct this invalid state after this step.
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
    protected virtual void Validate(Type? type, VectorStoreCollectionDefinition? definition)
    {
        if (this.KeyProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple key properties found on {TypeMessage()}the provided {nameof(VectorStoreCollectionDefinition)} while only one is supported.");
        }

        if (this.KeyProperties.Count == 0)
        {
            throw new NotSupportedException($"No key property found on {TypeMessage()}the provided {nameof(VectorStoreCollectionDefinition)} while at least one is required.");
        }

        if (this.Options.RequiresAtLeastOneVector && this.VectorProperties.Count == 0)
        {
            throw new NotSupportedException($"No vector property found on {TypeMessage()}the provided {nameof(VectorStoreCollectionDefinition)} while at least one is required.");
        }

        if (!this.Options.SupportsMultipleVectors && this.VectorProperties.Count > 1)
        {
            throw new NotSupportedException($"Multiple vector properties found on {TypeMessage()}the provided {nameof(VectorStoreCollectionDefinition)} while only one is supported.");
        }

        var storageNameMap = new Dictionary<string, PropertyModel>();

        foreach (var property in this.PropertyMap.Values)
        {
            this.ValidateProperty(property, definition);

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
    protected virtual void ValidateProperty(PropertyModel propertyModel, VectorStoreCollectionDefinition? definition)
    {
        var type = propertyModel.Type;

        Debug.Assert(propertyModel.Type is not null);

        switch (propertyModel)
        {
            case KeyPropertyModel keyProperty:
                if (keyProperty.IsAutoGenerated && !this.SupportsKeyAutoGeneration(keyProperty.Type))
                {
                    throw new NotSupportedException(
                        $"Property '{keyProperty.ModelName}' is configured for auto-generation, but key properties of type '{keyProperty.Type.Name}' do not support auto-generation.");
                }

                this.ValidateKeyProperty(keyProperty);
                break;

            case DataPropertyModel dataProperty:
                if (!this.IsDataPropertyTypeValid(dataProperty.Type, out var supportedTypes))
                {
                    throw new NotSupportedException(
                        $"Property '{dataProperty.ModelName}' has unsupported type '{type.Name}'. Data properties must be one of the supported types: {supportedTypes}.");
                }
                break;

            case VectorPropertyModel vectorProperty:
                if (vectorProperty.EmbeddingType is null)
                {
                    if (this.IsVectorPropertyTypeValid(vectorProperty.Type, out string? supportedVectorTypes))
                    {
                        throw new UnreachableException("EmbeddingType cannot be null when the property type is supported.");
                    }

                    if (vectorProperty.EmbeddingGenerator is null)
                    {
                        throw new InvalidOperationException(VectorDataStrings.UnsupportedVectorPropertyWithoutEmbeddingGenerator(vectorProperty));
                    }

                    // If the user has configured a desired embedding type (done to use en embedding type other than the provider's default one), throw errors tailored to that.
                    // Throw errors related to that.
                    var userRequestedEmbeddingType = definition?.Properties.OfType<VectorStoreVectorProperty>().SingleOrDefault(p => p.Name == vectorProperty.ModelName)?.EmbeddingType;
                    if (userRequestedEmbeddingType is not null)
                    {
                        throw new InvalidOperationException(this.IsVectorPropertyTypeValid(userRequestedEmbeddingType, out _)
                            ? VectorDataStrings.ConfiguredEmbeddingTypeIsUnsupportedByTheGenerator(vectorProperty, userRequestedEmbeddingType, supportedVectorTypes)
                            : VectorDataStrings.ConfiguredEmbeddingTypeIsUnsupportedByTheProvider(vectorProperty, userRequestedEmbeddingType, supportedVectorTypes));
                    }

                    throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGenerator(vectorProperty, vectorProperty.EmbeddingGenerator, supportedVectorTypes));
                }

                if (!this.IsVectorPropertyTypeValid(vectorProperty.EmbeddingType, out string? supportedVectorTypes2))
                {
                    // Should in principle never happen, only with incorrect provider customization.
                    throw new InvalidOperationException($"Property '{vectorProperty.ModelName}' has unsupported embedding type '{vectorProperty.EmbeddingType.Name}'. Vector properties must be one of the supported types: {supportedVectorTypes2}.");
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
    /// Configures auto-generation for the given key property.
    /// Defaults to configuring <see cref="Guid" /> key properties as auto-generated, and throwing if auto-generation is requested for
    /// any other type.
    /// </summary>
    protected virtual bool SupportsKeyAutoGeneration(Type keyPropertyType)
        => keyPropertyType == typeof(Guid);

    /// <summary>
    /// Validates the key property. The default implementation validates that the collection's generic key type (<see cref="KeyType"/>)
    /// corresponds to the key property type on the model, if <see cref="KeyType"/> was provided.
    /// Provider overrides should call the base implementation.
    /// </summary>
    protected virtual void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        if (this.KeyType is not null && this.KeyType != typeof(object) && this.KeyType != keyProperty.Type)
        {
            throw new InvalidOperationException(
                $"The collection's generic key type is '{this.KeyType.Name}', but the key property '{keyProperty.ModelName}' has type '{keyProperty.Type.Name}'. The generic key type must match the key property type.");
        }
    }

    /// <summary>
    /// Validates that the .NET type for a data property is supported by the provider.
    /// </summary>
    protected abstract bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes);

    /// <summary>
    /// Validates that the .NET type for a vector property is supported by the provider.
    /// </summary>
    protected abstract bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes);
}
