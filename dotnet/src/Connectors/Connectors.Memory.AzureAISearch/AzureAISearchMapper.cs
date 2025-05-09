// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json.Nodes;
using System.Text.Json;
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

        // Go over the vector properties; those which have an embedding generator configured on them will have embedding generators, overwrite
        // the value in the JSON object with that.
        if (generatedEmbeddings is not null)
        {
            for (var i = 0; i < model.VectorProperties.Count; i++)
            {
                if (generatedEmbeddings?[i]?[recordIndex] is MEAI.Embedding embedding)
                {
                    var property = model.VectorProperties[i];

                    Debug.Assert(property.EmbeddingGenerator is not null);

                    jsonObject[property.StorageName] = embedding switch
                    {
                        MEAI.Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        MEAI.Embedding<byte> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        MEAI.Embedding<sbyte> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        _ => throw new UnreachableException()
                    };
                }
            }
        }

        return jsonObject;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, bool includeVectors)
    {
        return storageModel.Deserialize<TRecord>(jsonSerializerOptions)!;
    }
}
