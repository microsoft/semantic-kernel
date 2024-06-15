// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.redis;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryRecord;
import java.time.ZonedDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import redis.clients.jedis.search.Document;

/** Represents an entry in the Semantic Kernel Memory Table. */
public class RedisMemoryRecord extends JsonMemoryRecord {

    public RedisMemoryRecord(
            String id,
            String text,
            String description,
            String additionalMetadata,
            List<Float> embedding,
            String externalSourceName,
            boolean isReference) {
        super(
                id,
                text,
                description,
                additionalMetadata,
                embedding,
                externalSourceName,
                isReference);
    }

    /**
     * Converts a RedisSearch Document to a HashMap.
     *
     * @param document A Redis Search Document
     * @return A HashMap containing the iterator's entries
     */
    protected Map<String, Object> documentToMap(Document document) {
        return StreamSupport.stream(document.getProperties().spliterator(), false)
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
    }

    /**
     * Gets the embedding information associated with the entry.
     *
     * @param map A hashmap with keys representing a record
     * @param withEmbedding A boolean flag indicating that the embedding should be returned with the
     *     metadata
     * @return A MemoryRecord object.
     */
    public static MemoryRecord mapToRecord(Map<String, String> map, boolean withEmbedding) {
        Embedding embedding = Embedding.empty();
        ZonedDateTime time = null;
        ObjectMapper mapper = new ObjectMapper();
        try {
            if (map.get(TIME) != null) {
                time =
                        mapper.readValue(
                                map.getOrDefault(TIME, ZonedDateTime.now().toString()),
                                ZonedDateTime.class);
            }
            if (withEmbedding) {
                List<Float> embeddings = mapper.readValue(map.get(EMBEDDING), List.class);
                embedding = new Embedding(embeddings);
            }
        } catch (JsonProcessingException e) {
            throw new RedisException(
                    RedisException.ErrorCodes.REDIS_ERROR, "Error deserializing Redis entry", e);
        }

        return MemoryRecord.localRecord(
                map.get(ID),
                map.get(TEXT),
                map.get(DESCRIPTION),
                embedding,
                map.get(ADDITIONAL_METADATA),
                map.get(EXTERNAL_SOURCE_NAME),
                time);
    }

    /**
     * Gets the embedding information associated with the entry.
     *
     * @param record A MemoryRecord object
     * @return A hashmap containing the entries of the record.
     */
    public static Map<String, Object> recordToMap(MemoryRecord record) {

        Map<String, Object> map = new HashMap<String, Object>();

        map.put(ID, record.getMetadata().getId());
        map.put(EXTERNAL_SOURCE_NAME, record.getMetadata().getExternalSourceName());
        map.put(TEXT, record.getMetadata().getText());
        map.put(DESCRIPTION, record.getMetadata().getDescription());
        map.put(EMBEDDING, record.getEmbedding().getVector());
        map.put(ADDITIONAL_METADATA, record.getMetadata().getAdditionalMetadata());
        map.put(IS_REFERENCE, record.getMetadata().isReference());

        return map;
    }
}
