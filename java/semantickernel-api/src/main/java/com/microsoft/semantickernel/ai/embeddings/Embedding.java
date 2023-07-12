// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/** Represents a strongly typed vector of numeric data. */
public class Embedding<EmbeddingType extends Number> {

    public List<EmbeddingType> getVector() {
        return Collections.unmodifiableList(vector);
    }

    private final List<EmbeddingType> vector;

    private static final Embedding<Number> EMPTY =
            new Embedding(Collections.unmodifiableList(new ArrayList<>()));

    @SuppressWarnings("unchecked")
    public static <EmbeddingType extends Number> Embedding<EmbeddingType> empty() {
        return (Embedding<EmbeddingType>) EMPTY;
    }

    /** Initializes a new instance of the Embedding class. */
    public Embedding() {
        this.vector = Collections.emptyList();
    }

    /**
     * Initializes a new instance of the Embedding class that contains numeric elements copied from
     * the specified collection
     *
     * @param vector The collection whose elements are copied to the new Embedding
     */
    public Embedding(List<EmbeddingType> vector) {
        //        Verify.NotNull(vector, nameof(vector));
        this.vector =
                vector != null ? Collections.unmodifiableList(vector) : Collections.emptyList();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Embedding)) return false;

        Embedding<?> embedding = (Embedding<?>) o;

        return vector.equals(embedding.vector);
    }

    @Override
    public int hashCode() {
        return vector.hashCode();
    }

    @Override
    public String toString() {
        return "Embedding{"
                + "vector="
                + vector.stream()
                        .limit(3)
                        .map(String::valueOf)
                        .collect(Collectors.joining(", ", "[", vector.size() > 3 ? "...]" : "]"))
                + '}';
    }
}
