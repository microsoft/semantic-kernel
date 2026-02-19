// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal sealed class AzureAISearchMapper<TRecord>(CollectionModel model, JsonSerializerOptions? jsonSerializerOptions) : IAzureAISearchMapper<TRecord>
    where TRecord : class
{
    public JsonObject MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings)
    {
        Verify.NotNull(dataModel);

        var jsonObject = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        // Azure AI Search only supports Edm.DateTimeOffset for date/time types.
        // DateTime properties may be serialized by STJ without timezone info (when Kind=Unspecified),
        // which Azure AI Search rejects. Convert them to DateTimeOffset (UTC).
        // DateOnly properties are serialized as "yyyy-MM-dd", which also isn't accepted.
        // Convert them to full DateTimeOffset representation (midnight UTC).
        foreach (var dataProperty in model.DataProperties)
        {
            var propertyType = Nullable.GetUnderlyingType(dataProperty.Type) ?? dataProperty.Type;

            if (propertyType == typeof(DateTime) && jsonObject.TryGetPropertyValue(dataProperty.StorageName, out var dtNode) && dtNode is not null)
            {
                var dateTime = dtNode.Deserialize<DateTime>(jsonSerializerOptions);
                jsonObject[dataProperty.StorageName] = JsonValue.Create(new DateTimeOffset(DateTime.SpecifyKind(dateTime, DateTimeKind.Utc), TimeSpan.Zero));
            }
#if NET
            else if (propertyType == typeof(DateOnly) && jsonObject.TryGetPropertyValue(dataProperty.StorageName, out var dateNode) && dateNode is not null)
            {
                var dateOnly = dateNode.Deserialize<DateOnly>(jsonSerializerOptions);
                jsonObject[dataProperty.StorageName] = JsonValue.Create(new DateTimeOffset(dateOnly.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero));
            }
#endif
        }

        // Go over the vector properties; inject any generated embeddings to overwrite the JSON serialized above.
        // Also, for Embedding<T> properties we also need to overwrite with a simple array (since Embedding<T> gets serialized as a complex object).
        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            Embedding<float>? embedding = generatedEmbeddings?[i]?[recordIndex] is Embedding ge ? (Embedding<float>)ge : null;

            if (embedding is null)
            {
                switch (Nullable.GetUnderlyingType(property.Type) ?? property.Type)
                {
                    case var t when t == typeof(ReadOnlyMemory<float>):
                    case var t2 when t2 == typeof(float[]):
                        // The .NET vector property is a ReadOnlyMemory<float> or float[] (not an Embedding), which means that JsonSerializer
                        // already serialized it correctly above.
                        // In addition, there's no generated embedding (which would be an Embedding which we'd need to handle manually).
                        // So there's nothing for us to do.
                        continue;

                    case var t when t == typeof(Embedding<float>):
                        embedding = (Embedding<float>)property.GetValueAsObject(dataModel)!;
                        break;

                    default:
                        throw new UnreachableException();
                }
            }

            var jsonArray = new JsonArray();

            foreach (var item in embedding.Vector.Span)
            {
                jsonArray.Add(JsonValue.Create(item));
            }

            jsonObject[property.StorageName] = jsonArray;
        }

        return jsonObject;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, bool includeVectors)
    {
        // Azure AI Search stores DateTime properties as Edm.DateTimeOffset.
        // Convert them back to DateTime so STJ can deserialize them into the correct type.
        // DateOnly properties also need to be converted back from DateTimeOffset.
        foreach (var dataProperty in model.DataProperties)
        {
            var propertyType = Nullable.GetUnderlyingType(dataProperty.Type) ?? dataProperty.Type;

            if (propertyType == typeof(DateTime) && storageModel.TryGetPropertyValue(dataProperty.StorageName, out var dtNode) && dtNode is not null)
            {
                var dateTimeOffset = dtNode.Deserialize<DateTimeOffset>(jsonSerializerOptions);
                storageModel[dataProperty.StorageName] = JsonValue.Create(dateTimeOffset.UtcDateTime);
            }
#if NET
            else if (propertyType == typeof(DateOnly) && storageModel.TryGetPropertyValue(dataProperty.StorageName, out var dateNode) && dateNode is not null)
            {
                var dateTimeOffset = dateNode.Deserialize<DateTimeOffset>(jsonSerializerOptions);
                storageModel[dataProperty.StorageName] = JsonValue.Create(DateOnly.FromDateTime(dateTimeOffset.DateTime));
            }
#endif
        }

        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                // If the vector property .NET type is Embedding<float>, we need to create the JSON structure for it
                // (JSON array embedded inside an object representing the embedding), so that the deserialization below
                // works correctly.
                if (vectorProperty.Type == typeof(Embedding<float>))
                {
                    var arrayNode = storageModel[vectorProperty.StorageName];
                    if (arrayNode is not null)
                    {
                        storageModel[vectorProperty.StorageName] = new JsonObject
                        {
                            [nameof(Embedding<float>.Vector)] = arrayNode.DeepClone()
                        };
                    }
                }
            }
        }

        return storageModel.Deserialize<TRecord>(jsonSerializerOptions)!;
    }
}
