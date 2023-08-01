// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.EmbeddingVector;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

import java.util.Arrays;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.StringJoiner;
import java.util.stream.Collectors;

/**
 * This sample provides a custom implementation of {@code MemoryStore} that is read only.
 * In this sample, the data is stored in a JSON String and deserialized into an
 * {@code MemoryRecord[]}. For this specific sample, the implementation
 * of {@code MemoryStore}  has a single collection, and thus does not need to be named.
 * It also assumes that the JSON formatted data can be deserialized into {@code MemoryRecord} objects.
 * @see MemoryRecord
 * @see MemoryStore
 */
public class Example25_ReadOnlyMemoryStore
{
    public static void main(String[] args) {
        RunAsync().block();
    }

    public static Mono<Void> RunAsync()
    {
        var store = new ReadOnlyMemoryStore(JSON_VECTOR_ENTRIES);

        var embedding = new Embedding<Float>(Arrays.asList(22f, 4f, 6f));

        System.out.println("Reading data from custom read-only memory store");
        Mono<?> mono = store.getAsync("collection", "key3", true)
                .mapNotNull(memoryRecord -> {
                    String memoryRecordId = memoryRecord.getMetadata().getId();
                    Embedding<? extends Number> memoryRecordEmbedding = memoryRecord.getEmbedding();
                    System.out.printf("ID = %s, Embedding = %s%n", memoryRecordId, embeddingVectorToString(memoryRecordEmbedding));
                    return memoryRecord;
                });

        mono = mono.then(
                store.getNearestMatchAsync("collection", embedding, 0.0, true)
                        .mapNotNull(result -> {
                                    Float similarity = result.getT2().floatValue();
                                    MemoryRecord memoryRecord = result.getT1();
                                    Embedding<? extends Number> memoryRecordEmbedding = memoryRecord.getEmbedding();
                                    System.out.printf("Embedding = %s, Similarity = %f%n", embeddingVectorToString(memoryRecordEmbedding), similarity);
                                    return result;
                                }
                        )
        );

        return mono.then();

    }

    private static String embeddingVectorToString(Embedding<? extends Number> embedding) {
        StringJoiner stringJoiner = new StringJoiner(", ", "[", "]");
        embedding.getVector().stream().map(Number::toString).forEach(stringJoiner::add);
        return stringJoiner.toString();
    }

    private static List<Float> toFloatList(List<? extends Number> list) {
        return list.stream().map(Number::floatValue).collect(Collectors.toList());
    }

    private static class ReadOnlyMemoryStore implements MemoryStore
    {
        private final MemoryRecord[] _memoryRecords;
        private final int _vectorSize = 3;

        public ReadOnlyMemoryStore(String valueString)
        {
            try {
                _memoryRecords = new ObjectMapper().readValue(valueString, MemoryRecord[].class);
            } catch (JsonProcessingException e) {
                throw new RuntimeException("Unable to deserialize memory records");
            }
        }

        @Override
        public Mono<Void> createCollectionAsync(String collectionName)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<Void> deleteCollectionAsync(String collectionName)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<Boolean> doesCollectionExistAsync(String collectionName)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<MemoryRecord> getAsync(String collectionName, String key, boolean withEmbedding)
        {
            // Note: with this simple implementation, the MemoryRecord will always contain the embedding.
            return Mono.justOrEmpty(
                    Arrays.stream(this._memoryRecords)
                            .filter(it -> it.getKey().equals(key))
                            .findFirst()
            );
        }

        @Override
        public Mono<Collection<MemoryRecord>> getBatchAsync(String collectionName, Collection<String> keys, boolean withEmbeddings)
        {
            // Note: with this simple implementation, the MemoryRecord will always contain the embedding.
            return Mono.just(
                    Arrays.stream(this._memoryRecords)
                            .filter(it -> keys.contains(it.getKey()))
                            .collect(Collectors.toList())
            );
        }

        @Override
        public Mono<List<String>> getCollectionsAsync()
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<Tuple2<MemoryRecord, ? extends Number>> getNearestMatchAsync(String collectionName, Embedding<? extends Number> embedding, double minRelevanceScore,
                                                                        boolean withEmbedding)
        {
            // Note: with this simple implementation, the MemoryRecord will always contain the embedding.
            final EmbeddingVector<Float> embeddingVector = new EmbeddingVector<>(toFloatList(embedding.getVector()));
            return Mono.justOrEmpty(
            Arrays.stream(this._memoryRecords)
                    .map(it -> {
                        EmbeddingVector<Float> memoryRecordEmbeddingVector =
                                new EmbeddingVector<>(toFloatList(it.getEmbedding().getVector()));
                        double cosineSimilarity = -1d;
                        try {
                            cosineSimilarity = memoryRecordEmbeddingVector.cosineSimilarity(embeddingVector);
                        } catch (IllegalArgumentException e) {
                            // Vectors cannot have zero norm
                        }
                        return Tuples.of(it, cosineSimilarity);
                    })
                    .filter(it -> it.getT2() >= minRelevanceScore)
                    .max(Comparator.comparing(Tuple2::getT2, Double::compare))
            );
        }

        @Override
        public Mono<Collection<Tuple2<MemoryRecord, Number>>> getNearestMatchesAsync(String collectionName, Embedding<? extends Number> embedding, int limit,
            double minRelevanceScore, boolean withEmbeddings)
        {
            // Note: with this simple implementation, the MemoryRecord will always contain the embedding.
            final EmbeddingVector<Float> embeddingVector = new EmbeddingVector<>(toFloatList(embedding.getVector()));
            return Mono.justOrEmpty(
                    Arrays.stream(this._memoryRecords)
                            .map(it -> {
                                EmbeddingVector<Float> memoryRecordEmbeddingVector =
                                        new EmbeddingVector<>(toFloatList(it.getEmbedding().getVector()));
                                double cosineSimilarity = -1d;
                                try {
                                    cosineSimilarity = memoryRecordEmbeddingVector.cosineSimilarity(embeddingVector);
                                } catch (IllegalArgumentException e) {
                                    // Vectors cannot have zero norm
                                }
                                return Tuples.of(it, (Number)cosineSimilarity);
                            })
                            .filter(it -> it.getT2().doubleValue() >= minRelevanceScore)
                            // sort by similarity score, descending
                            .sorted(Comparator.comparing(it -> it.getT2().doubleValue(), (a,b) -> Double.compare(b, a)))
                            .limit(limit)
                            .collect(Collectors.toList())
            );


        }

        @Override
        public Mono<Void> removeAsync(String collectionName, String key)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<Void> removeBatchAsync(String collectionName, Collection<String> keys)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<String> upsertAsync(String collectionName, MemoryRecord record)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }

        @Override
        public Mono<Collection<String>> upsertBatchAsync(String collectionName, Collection<MemoryRecord> records)
        {
            return Mono.error(() -> new UnsupportedOperationException("This is a read-only memory store"));
        }
    }

    private static final String JSON_VECTOR_ENTRIES = """
    [
        {
            "embedding": {
                "vector": [0, 0, 0 ]
            },
            "metadata": {
                "is_reference": false,
                "external_source_name": "externalSourceName",
                "id": "Id1",
                "description": "description",
                "text": "text",
                "additional_metadata" : "value:"
            },
            "key": "key1",
            "timestamp": null
         },
         {
            "embedding": {
                "vector": [0, 0, 10 ]
            },
            "metadata": {
                "is_reference": false,
                "external_source_name": "externalSourceName",
                "id": "Id2",
                "description": "description",
                "text": "text",
                "additional_metadata" : "value:"
            },
            "key": "key2",
            "timestamp": null
         },
         {
            "embedding": {
                "vector": [1, 2, 3 ]
            },
            "metadata": {
                "is_reference": false,
                "external_source_name": "externalSourceName",
                "id": "Id3",
                "description": "description",
                "text": "text",
                "additional_metadata" : "value:"
            },
            "key": "key3",
            "timestamp": null
         },
         {
            "embedding": {
                "vector": [-1, -2, -3 ]
            },
            "metadata": {
                "is_reference": false,
                "external_source_name": "externalSourceName",
                "id": "Id4",
                "description": "description",
                "text": "text",
                "additional_metadata" : "value:"
            },
            "key": "key4",
            "timestamp": null
         },
         {
            "embedding": {
                "vector": [12, 8, 4 ]
            },
            "metadata": {
                "is_reference": false,
                "external_source_name": "externalSourceName",
                "id": "Id5",
                "description": "description",
                "text": "text",
                "additional_metadata" : "value:"
            },
            "key": "key5",
            "timestamp": null
        }
    ]
    """.replaceAll(" |\\n", "");
}
