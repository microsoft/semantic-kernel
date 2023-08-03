// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonGetter;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.StdSerializer;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/** Represents a strongly typed vector of numeric data. */
public class Embedding {

    private final EmbeddingVector vector;

    private static final Embedding EMPTY =
            new Embedding(Collections.unmodifiableList(new ArrayList<>()));

    public static Embedding empty() {
        return EMPTY;
    }

    /** Initializes a new instance of the Embedding class. */
    public Embedding() {
        this.vector = new EmbeddingVector();
    }

    /**
     * Initializes a new instance of the Embedding class that contains numeric elements copied from
     * the specified collection
     *
     * @param vector The collection whose elements are copied to the new Embedding
     */
    @JsonCreator
    public Embedding(@JsonProperty("vector") List<Float> vector) {
        //        Verify.NotNull(vector, nameof(vector));
        this.vector = new EmbeddingVector(vector);
    }

    @JsonIgnore
    public EmbeddingVector getVector() {
        return vector;
    }

    @JsonGetter("vector")
    public List<Float> getRawVector() {
        return vector.getVector();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Embedding)) return false;

        Embedding embedding = (Embedding) o;

        return getRawVector().equals(embedding.getRawVector());
    }

    @Override
    public int hashCode() {
        return getRawVector().hashCode();
    }

    @Override
    public String toString() {
        return "Embedding{"
                + "vector="
                + vector.getVector().stream()
                        .limit(3)
                        .map(String::valueOf)
                        .collect(Collectors.joining(", ", "[", vector.size() > 3 ? "...]" : "]"))
                + '}';
    }
}
