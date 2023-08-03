// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai;

import com.microsoft.semantickernel.ai.vectoroperations.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Represents a strongly typed vector of numeric data
 **/
public class EmbeddingVector
        implements DotProduct,
                EuclideanLength,
                CosineSimilarity,
                Multiply,
                Divide,
                Normalize {

    private final List<Float> vector;

    public EmbeddingVector(List<Float> vector) {
        this.vector = Collections.unmodifiableList(vector);
    }

    public EmbeddingVector(Float vector) {
        this.vector = Collections.unmodifiableList(Arrays.asList(vector));
    }

    public EmbeddingVector() {
        this.vector = Collections.unmodifiableList(new ArrayList<>());
    }

    /**
     * Size of the vector
     *
     * @return Vector's size
     */
    public int size() {
        return this.vector.size();
    }

    public List<Float> getVector() {
        return Collections.unmodifiableList(this.vector);
    }

    /**
     * Calculates the dot product of this vector with another.
     *
     * @param other The other vector to compute the dot product with
     * @return Dot product between vectors
     */
    @Override
    public float dot(EmbeddingVector other) {
        if (this.size() != other.size()) {
            throw new IllegalArgumentException("Vectors lengths must be equal");
        }

        float result = 0;
        for (int i = 0; i < this.size(); ++i) {
            result += this.vector.get(i) * other.getVector().get(i);
        }

        return result;
    }

    /**
     * Calculates the Euclidean length of this vector.
     *
     * @return Euclidean length
     */
    @Override
    public float euclideanLength() {
        return (float) Math.sqrt(this.dot(this));
    }

    /**
     * Calculates the cosine similarity of this vector with another.
     *
     * @param other The other vector to compute cosine similarity with.
     * @return Cosine similarity between vectors
     */
    @Override
    public float cosineSimilarity(EmbeddingVector other) {
        if (this.size() != other.size()) {
            throw new IllegalArgumentException("Vectors lengths must be equal");
        }

        float dotProduct = this.dot(other);
        float normX = this.dot(this);
        float normY = other.dot(other);

        if (normX == 0 || normY == 0) {
            throw new IllegalArgumentException("Vectors cannot have zero norm");
        }

        return dotProduct / (float)(Math.sqrt(normX) * Math.sqrt(normY));
    }

    @Override
    public EmbeddingVector multiply(float multiplier) {
        List<Float> result =
                this.getVector().stream()
                        .map(x -> x * multiplier)
                        .collect(Collectors.toList());

        return (EmbeddingVector) new EmbeddingVector(result);
    }

    @Override
    public EmbeddingVector divide(float divisor) {
        if (Float.isNaN(divisor) || divisor == 0) {
            throw new IllegalArgumentException("Divisor cannot be zero");
        }

        List<Float> result =
                this.getVector().stream()
                        .map(x -> x / divisor)
                        .collect(Collectors.toList());

        return new EmbeddingVector(result);
    }

    /**
     * Normalizes the underlying vector, such that the Euclidean length is 1.
     *
     * @return Normalized embedding
     */
    @Override
    public EmbeddingVector normalize() {
        return this.divide(this.euclideanLength());
    }
}
