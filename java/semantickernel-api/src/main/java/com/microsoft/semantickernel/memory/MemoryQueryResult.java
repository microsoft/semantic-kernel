// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import javax.annotation.Nonnull;

/** Copy of metadata associated with a memory entry. */
public class MemoryQueryResult {
    /**
     * Whether the source data used to calculate embeddings are stored in the local storage provider
     * or is available through an external service, such as website, MS Graph, etc.
     */
    @Nonnull private final MemoryRecordMetadata metadata;

    /** Search relevance, from 0 to 1, where 1 means perfect match. */
    private final double relevance;

    /**
     * Create a new instance of MemoryQueryResult
     *
     * @param metadata Whether the source data used to calculate embeddings are stored in the local
     *     storage provider or is available through an external service, such as website, MS Graph,
     *     etc.
     * @param relevance Search relevance, from 0 to 1, where 1 means perfect match.
     */
    public MemoryQueryResult(@Nonnull MemoryRecordMetadata metadata, double relevance) {
        this.metadata = metadata;
        this.relevance = clampRelevance(relevance);
    }

    public MemoryRecordMetadata getMetadata() {
        return metadata;
    }

    public double getRelevance() {
        return relevance;
    }

    // function to clamp relevance to [0, 1]
    private static double clampRelevance(double relevance) {
        return !Double.isNaN(relevance) ? Math.max(0, Math.min(1, relevance)) : 0d;
    }

    /*
    /// <summary>
    /// Create a new instance of MemoryQueryResult from a json string representing MemoryRecord metadata.
    /// </summary>
    /// <param name="json">The json string to deserialize.</param>
    /// <param name="relevance">The similarity score associated with the result.</param>
    /// <returns>A new instance of MemoryQueryResult.</returns>
    /// <exception cref="MemoryException"></exception>
    public static MemoryQueryResult FromJsonMetadata(
        string json,
        double relevance)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
        if (metadata != null)
        {
            return new MemoryQueryResult(metadata, relevance);
        }
        else
        {
            throw new MemoryException(
                MemoryException.ErrorCodes.UnableToDeserializeMetadata,
                "Unable to create memory query result from serialized metadata");
        }
    }

    internal static MemoryQueryResult FromMemoryRecord(
        MemoryRecord rec,
        double relevance)
    {
        return new MemoryQueryResult(
            (MemoryRecordMetadata)rec.Metadata.Clone(),
            relevance);
    }

     */
}
