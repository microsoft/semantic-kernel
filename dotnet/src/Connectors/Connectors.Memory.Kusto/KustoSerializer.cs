// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

/// <summary>
/// Contains serialization/deserialization logic for memory record properties in Kusto.
/// </summary>
public static class KustoSerializer
{
    /// <summary>
    /// Returns serialized string from an embedding instance.
    /// </summary>
    /// <param name="embedding">Instance of an embedding for serialization.</param>
    public static string SerializeEmbedding(ReadOnlyMemory<float> embedding)
    {
        return JsonSerializer.Serialize(embedding, s_jsonSerializerOptions);
    }

    /// <summary>
    /// Returns deserialized instance of an embedding from serialized embedding.
    /// </summary>
    /// <param name="embedding">Serialized embedding.</param>
    public static ReadOnlyMemory<float> DeserializeEmbedding(string? embedding)
    {
        return string.IsNullOrEmpty(embedding) ?
            default :
            JsonSerializer.Deserialize<ReadOnlyMemory<float>>(embedding!, s_jsonSerializerOptions);
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

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = CreateSerializerOptions();

    private static JsonSerializerOptions CreateSerializerOptions()
    {
        var jso = new JsonSerializerOptions();
        jso.Converters.Add(new ReadOnlyMemoryConverter());
        return jso;
    }

    #endregion
}
