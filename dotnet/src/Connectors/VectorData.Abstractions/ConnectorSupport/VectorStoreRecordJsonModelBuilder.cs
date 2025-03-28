// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// A model builder that performs logic specific to connectors which use System.Text.Json for serialization.
/// </summary>
public class VectorStoreRecordJsonModelBuilder(VectorStoreRecordModelBuildingOptions options)
    : VectorStoreRecordModelBuilder(EnableCustomSerialization(options))
{
    private JsonSerializerOptions _jsonSerializerOptions = JsonSerializerOptions.Default;

    private static VectorStoreRecordModelBuildingOptions EnableCustomSerialization(VectorStoreRecordModelBuildingOptions options)
    {
        options.UsesExternalSerializer = true;

        return options;
    }

    /// <summary>
    /// Builds and returns an <see cref="VectorStoreRecordModel"/> from the given <paramref name="clrType"/> and <paramref name="vectorStoreRecordDefinition"/>.
    /// </summary>
    public virtual VectorStoreRecordModel Build(Type clrType, VectorStoreRecordDefinition? vectorStoreRecordDefinition, JsonSerializerOptions? jsonSerializerOptions)
    {
        if (jsonSerializerOptions is not null)
        {
            this._jsonSerializerOptions = jsonSerializerOptions;
        }

        return this.Build(clrType, vectorStoreRecordDefinition);
    }

    /// <inheritdoc/>
    protected override void Customize()
    {
        // This mimics the naming behavior of the System.Text.Json serializer, which we use for serialization/deserialization.
        // The property storage names in the model must in sync with the serializer configuration, since the model is used e.g. for filtering
        // even if serialization/deserialization doesn't use the model.
        foreach (var property in this.Properties)
        {
            var keyPropertyWithReservedName = this.Options.ReservedKeyStorageName is not null && property is VectorStoreRecordKeyPropertyModel;

            if (property.ClrProperty?.GetCustomAttribute<JsonPropertyNameAttribute>() is { } jsonPropertyNameAttribute)
            {
                if (keyPropertyWithReservedName)
                {
                    throw new InvalidOperationException($"The key property for your connector must always have the reserved name '{this.Options.ReservedKeyStorageName}' and cannot be changed.");
                }

                property.StorageName = jsonPropertyNameAttribute.Name;
            }
            else if (this._jsonSerializerOptions.PropertyNamingPolicy is { } namingPolicy)
            {
                property.StorageName = namingPolicy.ConvertName(property.ModelName);
            }

            if (keyPropertyWithReservedName)
            {
                // Somewhat hacky:
                // Some providers (Weaviate, Cosmos NoSQL) have a fixed, reserved storage name for keys (id), and at the same time use an external
                // JSON serializer to serialize the entire user POCO. Since the serializer is unaware of the reserved storage name, it will produce
                // a storage name as usual, based on the CLR property's name, possibly with a naming policy applied to it. The connector then needs
                // to look that up and replace with the reserved name.
                // So we store the policy-transformed name, as StorageName will be overwritten later with the reserved name.
                property.TemporaryStorageName = property.StorageName;
            }
        }
    }
}
