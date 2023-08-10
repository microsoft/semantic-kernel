// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

/// <summary>
/// Contains serialization/deserialization logic for memory record properties in Kusto.
/// </summary>
public static class KustoSerializer
{
    /// <summary>
    /// Returns serialized string from <see cref="Embedding{TEmbedding}"/> instance.
    /// </summary>
    /// <param name="embedding">Instance of <see cref="Embedding{TEmbedding}"/> for serialization.</param>
    public static string SerializeEmbedding(Embedding<float> embedding)
    {
        return JsonSerializer.Serialize(embedding.Vector);
    }

    /// <summary>
    /// Returns deserialized instance of <see cref="Embedding{TEmbedding}"/> from serialized embedding.
    /// </summary>
    /// <param name="embedding">Serialized embedding.</param>
    public static Embedding<float> DeserializeEmbedding(string? embedding)
    {
        if (string.IsNullOrEmpty(embedding))
        {
            return default;
        }

        float[]? floatArray = JsonSerializer.Deserialize<float[]>(embedding!);

        if (floatArray == null)
        {
            return default;
        }

        return new Embedding<float>(floatArray);
    }

    /// <summary>
    /// Returns serialized string from <see cref="MemoryRecordMetadata"/> instance.
    /// </summary>
    /// <param name="metadata">Instance of <see cref="MemoryRecordMetadata"/> for serialization.</param>
    public static string SerializeMetadata(MemoryRecordMetadata metadata)
    {
        if (metadata == null)
        {
            return string.Empty;
        }

        return JsonSerializer.Serialize(metadata);
    }

    /// <summary>
    /// Returns deserialized instance of <see cref="MemoryRecordMetadata"/> from serialized metadata.
    /// </summary>
    /// <param name="metadata">Serialized metadata.</param>
    public static MemoryRecordMetadata DeserializeMetadata(string metadata)
    {
        return JsonSerializer.Deserialize<MemoryRecordMetadata>(metadata)!;
    }

    /// <summary>
    /// Returns serialized string from <see cref="DateTimeOffset"/> instance.
    /// </summary>
    /// <param name="dateTimeOffset">Instance of <see cref="DateTimeOffset"/> for serialization.</param>
    public static string SerializeDateTimeOffset(DateTimeOffset? dateTimeOffset)
    {
        if (dateTimeOffset == null)
        {
            return string.Empty;
        }

        return dateTimeOffset.Value.DateTime.ToString(TimestampFormat, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Returns deserialized instance of <see cref="DateTimeOffset"/> from serialized timestamp.
    /// </summary>
    /// <param name="dateTimeOffset">Serialized timestamp.</param>
    public static DateTimeOffset? DeserializeDateTimeOffset(string? dateTimeOffset)
    {
        if (string.IsNullOrWhiteSpace(dateTimeOffset))
        {
            return null;
        }

        if (DateTimeOffset.TryParseExact(dateTimeOffset, TimestampFormat, CultureInfo.InvariantCulture, DateTimeStyles.None, out DateTimeOffset result))
        {
            return result;
        }

        throw new InvalidCastException("Timestamp format cannot be parsed");
    }

    #region private ================================================================================

    private const string TimestampFormat = "yyyy-MM-ddTHH:mm:ssZ";

    #endregion
}
