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
