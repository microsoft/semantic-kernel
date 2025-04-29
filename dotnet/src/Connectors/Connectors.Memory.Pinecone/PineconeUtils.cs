// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Utils for Pinecone connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public static class PineconeUtils
{
    /// <summary>
    ///  The maximum size of the metadata associated with each vector.
    ///  See https://docs.pinecone.io/docs/metadata-filtering#supported-metadata-size
    /// </summary>
    public const int MaxMetadataSize = 40 * 1024;

    /// <summary>
    /// The default dimension for Pinecone vectors. Equivalent to text-embeddings-ada-002 dimension.
    /// </summary>
    public const int DefaultDimension = 1536;

    /// <summary>
    /// Default index name.
    /// </summary>
    public const string DefaultIndexName = "sk-index";

    /// <summary>
    /// Defaults to cosine similarity.
    /// </summary>
    public const IndexMetric DefaultIndexMetric = IndexMetric.Cosine;

    /// <summary>
    ///  The standard index type for Pinecone vectors.
    /// </summary>
    public const PodType DefaultPodType = PodType.P1X1;

    internal static JsonSerializerOptions DefaultSerializerOptions { get; } = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
        AllowTrailingCommas = false,
        ReadCommentHandling = JsonCommentHandling.Skip,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        UnknownTypeHandling = JsonUnknownTypeHandling.JsonNode,
        NumberHandling = JsonNumberHandling.AllowReadingFromString,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) },
    };

    /// <summary>
    ///  Utility method to ensure that the metadata size is not too large.
    ///  This is necessary because Pinecone has a limit on the size of the metadata
    ///  associated with each vector.
    /// </summary>
    /// <param name="documents"></param>
    /// <returns> A stream of documents with valid metadata. </returns>
    /// <remarks>
    ///  If the metadata size is too large, the document will be split into multiple documents.
    ///  The text field will be removed from the metadata and the document ID will be set to {document ID}-{split counter}
    ///  The text field will be added to the metadata of the split documents. The split documents will be returned in the
    ///  same order as the original document.
    /// </remarks>
    public static async IAsyncEnumerable<PineconeDocument> EnsureValidMetadataAsync(
        IAsyncEnumerable<PineconeDocument> documents)
    {
        await foreach (PineconeDocument document in documents.ConfigureAwait(false))
        {
            if (document.Metadata is null || GetMetadataSize(document.Metadata) <= MaxMetadataSize)
            {
                yield return document;

                continue;
            }

            if (!document.Metadata.TryGetValue("text", out object? value))
            {
                yield return document;

                continue;
            }

            string text = value as string ?? string.Empty;
            int textSize = Encoding.UTF8.GetByteCount(text);
            document.Metadata.Remove("text");
            int remainingMetadataSize = GetMetadataSize(document.Metadata);

            int splitCounter = 0;
            int textIndex = 0;

            while (textSize > 0)
            {
                int availableSpace = MaxMetadataSize - remainingMetadataSize;
                int textSplitSize = Math.Min(textSize, availableSpace);

                while (textSplitSize > 0 && Encoding.UTF8.GetByteCount(text.ToCharArray(textIndex, textSplitSize)) > availableSpace)
                {
                    textSplitSize--;
                }

                string splitText = text.Substring(textIndex, textSplitSize);
                textIndex += textSplitSize;
                textSize -= Encoding.UTF8.GetByteCount(splitText);

                PineconeDocument splitDocument = PineconeDocument.Create($"{document.Id}_{splitCounter}", document.Values)
                    .WithMetadata(new Dictionary<string, object>(document.Metadata))
                    .WithSparseValues(document.SparseValues);
                splitDocument.Metadata!["text"] = splitText;

                yield return splitDocument;

                splitCounter++;
            }
        }
    }

    /// <summary>
    ///  Utility method to split a stream of documents into batches of a given size.
    /// </summary>
    /// <param name="data"></param>
    /// <param name="batchSize"></param>
    /// <returns> A stream of upsert requests. </returns>
    /// <remarks>
    ///  The recommended batch size as per Pinecone documentation is 100.
    ///  See https://docs.pinecone.io/docs/insert-data#batching-upserts
    /// </remarks>
    internal static async IAsyncEnumerable<UpsertRequest> GetUpsertBatchesAsync(
        IAsyncEnumerable<PineconeDocument> data,
        int batchSize)
    {
        List<PineconeDocument> currentBatch = new(batchSize);
        int batchCounter = 0;

        await foreach (PineconeDocument record in data.ConfigureAwait(false))
        {
            currentBatch.Add(record);

            if (currentBatch.Count != batchSize)
            {
                continue;
            }

            yield return UpsertRequest.UpsertVectors(currentBatch);

            batchCounter++;
            currentBatch = new List<PineconeDocument>(batchSize);
        }

        if (currentBatch.Count == 0)
        {
            yield break;
        }

        yield return UpsertRequest.UpsertVectors(currentBatch);
    }

    private static int GetMetadataSize(Dictionary<string, object> metadata)
    {
        using MemoryStream stream = new();
        using Utf8JsonWriter writer = new(stream);

        JsonSerializer.Serialize(writer, metadata);

        return (int)stream.Length;
    }

    /// <summary>
    ///  Utility method to convert a dictionary of filters to the format expected by Pinecone.
    /// </summary>
    /// <param name="filter"></param>
    /// <returns></returns>
    /// <remarks>
    ///  This is necessary because Pinecone has a different format for filters using the MongoDB query language
    ///  operators. This method converts the filters to the format expected by Pinecone.
    /// </remarks>
    public static Dictionary<string, object> ConvertFilterToPineconeFilter(Dictionary<string, object> filter)
    {
        Dictionary<string, object> pineconeFilter = [];

        foreach (KeyValuePair<string, object> entry in filter)
        {
            pineconeFilter[entry.Key] = entry.Value switch
            {
                PineconeOperator op => op.ToDictionary(),
                IList list => new PineconeOperator("$in", list).ToDictionary(),

                DateTimeOffset dateTimeOffset => new PineconeOperator("$eq", dateTimeOffset.ToUnixTimeSeconds()).ToDictionary(),
                _ => new PineconeOperator("$eq", entry.Value).ToDictionary()
            };
        }

        return pineconeFilter;
    }

    /// <summary>
    /// Maps <see cref="IndexMetric"/> to its string representation.
    /// </summary>
    /// <param name="indexMetric">Value of <see cref="IndexMetric"/>.</param>
    /// <returns>String representation.</returns>
    public static string MetricTypeToString(IndexMetric indexMetric)
    {
        return indexMetric switch
        {
            IndexMetric.Cosine => "cosine",
            IndexMetric.Dotproduct => "dotProduct",
            IndexMetric.Euclidean => "euclidean",
            _ => string.Empty
        };
    }

    /// <summary>
    /// Maps <see cref="PodType"/> to its string representation.
    /// </summary>
    /// <param name="podType">Value of <see cref="PodType"/>.</param>
    /// <returns>String representation.</returns>
    public static string PodTypeToString(PodType podType)
    {
        return podType switch
        {
            PodType.P1X1 => "p1x1",
            PodType.P1X2 => "p1x2",
            PodType.P1X4 => "p1x4",
            PodType.P1X8 => "p1x8",
            PodType.P2X1 => "p2x1",
            PodType.P2X2 => "p2x2",
            PodType.P2X4 => "p2x4",
            PodType.P2X8 => "p2x8",
            PodType.S1X1 => "s1x1",
            PodType.S1X2 => "s1x2",
            PodType.S1X4 => "s1x4",
            PodType.S1X8 => "s1x8",
            PodType.Starter => "starter",
            PodType.Nano => "nano",
            _ => string.Empty
        };
    }

    /// <summary>
    /// Class for Pinecone filtering logic.
    /// </summary>
    public sealed class PineconeOperator
    {
        /// <summary>
        /// Filtering operator (e.g. $eq, $ne), see https://docs.pinecone.io/docs/metadata-filtering#metadata-query-language.
        /// </summary>
        public string Operator { get; }

        /// <summary>
        /// Filtering value.
        /// </summary>
        public object Value { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="PineconeOperator"/> class.
        /// </summary>
        /// <param name="op">Filtering operator.</param>
        /// <param name="value">Filtering value.</param>
        public PineconeOperator(string op, object value)
        {
            this.Operator = op;
            this.Value = value;
        }

        /// <summary>
        /// Converts instance of <see cref="PineconeOperator"/> to <see cref="Dictionary{TKey, TValue}"/>.
        /// </summary>
        public Dictionary<string, object> ToDictionary()
        {
            return new Dictionary<string, object>
            {
                {
                    this.Operator, this.Value
                }
            };
        }
    }
}
