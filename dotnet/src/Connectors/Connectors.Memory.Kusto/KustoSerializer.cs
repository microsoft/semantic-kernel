// Copyright (c) Microsoft. All rights reserved.

using System;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Newtonsoft.Json;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

public static class KustoSerializer
{
    public static string SerializeEmbedding(Embedding<float> embedding)
    {
        return JsonConvert.SerializeObject(embedding.Vector);
    }

    public static Embedding<float> DeserializeEmbedding(string? embedding)
    {
        if (string.IsNullOrEmpty(embedding))
        {
            return default;
        }

        float[]? floatArray = JsonConvert.DeserializeObject<float[]>(embedding!);

        if (floatArray == null)
        {
            return default;
        }

        return new Embedding<float>(floatArray);
    }

    public static string SerializeMetadata(MemoryRecordMetadata metadata)
    {
        if (metadata == null)
        {
            return string.Empty;
        }

        return JsonConvert.SerializeObject(metadata);
    }

    public static MemoryRecordMetadata DeserializeMetadata(string metadata)
    {
        return JsonConvert.DeserializeObject<MemoryRecordMetadata>(metadata)!;
    }

    public static string SerializeDateTime(DateTime? dt)
    {
        if (dt == null)
        {
            return string.Empty;
        }

        return dt.Value.ToUtc().ToString("yyyy-MM-ddTHH:mm:ssZ", System.Globalization.CultureInfo.InvariantCulture);
    }

    public static string SerializeDateTimeOffset(DateTimeOffset? dto)
    {
        if (dto == null)
        {
            return string.Empty;
        }

        return dto.Value.UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", System.Globalization.CultureInfo.InvariantCulture);
    }
}
