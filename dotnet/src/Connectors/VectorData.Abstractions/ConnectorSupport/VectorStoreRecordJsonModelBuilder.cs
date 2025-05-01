// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// A model builder that performs logic specific to connectors which use System.Text.Json for serialization.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordJsonModelBuilder : VectorStoreRecordModelBuilder
{
    private JsonSerializerOptions _jsonSerializerOptions = JsonSerializerOptions.Default;

    /// <summary>
    /// Constructs a new <see cref="VectorStoreRecordJsonModelBuilder"/>.
    /// </summary>
    public VectorStoreRecordJsonModelBuilder(VectorStoreRecordModelBuildingOptions options)
        : base(options)
    {
        if (!options.UsesExternalSerializer)
        {
            throw new ArgumentNullException(nameof(options), $"{nameof(options.UsesExternalSerializer)} must be set when using this model builder.");
        }
    }

    /// <summary>
    /// Builds and returns an <see cref="VectorStoreRecordModel"/> from the given <paramref name="type"/> and <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    public virtual VectorStoreRecordModel Build(
        Type type,
        VectorStoreRecordDefinition? vectorStoreRecordDefinition,
        IEmbeddingGenerator? defaultEmbeddingGenerator,
        JsonSerializerOptions? jsonSerializerOptions)
    {
        if (jsonSerializerOptions is not null)
        {
            this._jsonSerializerOptions = jsonSerializerOptions;
        }

        return this.Build(type, vectorStoreRecordDefinition, defaultEmbeddingGenerator);
    }

    /// <inheritdoc/>
    protected override void Customize()
    {
        // This mimics the naming behavior of the System.Text.Json serializer, which we use for serialization/deserialization.
        // The property storage names in the model must in sync with the serializer configuration, since the model is used e.g. for filtering
        // even if serialization/deserialization doesn't use the model.
        var namingPolicy = this._jsonSerializerOptions.PropertyNamingPolicy;

        foreach (var property in this.Properties)
        {
            var keyPropertyWithReservedName = this.Options.ReservedKeyStorageName is not null && property is VectorStoreRecordKeyPropertyModel;
            string storageName;

            if (property.PropertyInfo?.GetCustomAttribute<JsonPropertyNameAttribute>() is { } jsonPropertyNameAttribute)
            {
                if (keyPropertyWithReservedName && jsonPropertyNameAttribute.Name != this.Options.ReservedKeyStorageName)
                {
                    throw new InvalidOperationException($"The key property for your connector must always have the reserved name '{this.Options.ReservedKeyStorageName}' and cannot be changed.");
                }

                storageName = jsonPropertyNameAttribute.Name;
            }
            else if (namingPolicy is not null)
            {
                storageName = namingPolicy.ConvertName(property.ModelName);
            }
            else
            {
                storageName = property.ModelName;
            }

            if (keyPropertyWithReservedName)
            {
                // Somewhat hacky:
                // Some providers (Weaviate, Cosmos NoSQL) have a fixed, reserved storage name for keys (id), and at the same time use an external
                // JSON serializer to serialize the entire user POCO. Since the serializer is unaware of the reserved storage name, it will produce
                // a storage name as usual, based on the .NET property's name, possibly with a naming policy applied to it. The connector then needs
                // to look that up and replace with the reserved name.
                // So we store the policy-transformed name, as StorageName contains the reserved name.
                property.TemporaryStorageName = storageName;
            }
            else
            {
                property.StorageName = storageName;
            }
        }
    }
}
