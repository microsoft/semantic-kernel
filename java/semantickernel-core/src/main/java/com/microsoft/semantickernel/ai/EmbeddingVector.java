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
 *
 * @param <TEmbedding>
 */
public class EmbeddingVector<TEmbedding extends Number>
        implements DotProduct<TEmbedding>,
                EuclideanLength,
                CosineSimilarity<TEmbedding>,
                Multiply<TEmbedding>,
                Divide<TEmbedding>,
                Normalize<TEmbedding> {

    private final List<TEmbedding> vector;

    public EmbeddingVector(List<TEmbedding> vector) {
        this.vector = Collections.unmodifiableList(vector);
    }

    public EmbeddingVector(TEmbedding[] vector) {
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

    public List<TEmbedding> getVector() {
        return Collections.unmodifiableList(this.vector);
    }

    /**
     * Calculates the dot product of this vector with another.
     *
     * @param other The other vector to compute the dot product with
     * @return Dot product between vectors
     */
    @Override
    public double dot(EmbeddingVector<TEmbedding> other) {
        if (this.size() != other.size()) {
            throw new IllegalArgumentException("Vectors lengths must be equal");
        }

        double result = 0;
        for (int i = 0; i < this.size(); ++i) {
            result += this.vector.get(i).doubleValue() * other.getVector().get(i).doubleValue();
        }

        return result;
    }

    /**
     * Calculates the Euclidean length of this vector.
     *
     * @return Euclidean length
     */
    @Override
    public double euclideanLength() {
        return Math.sqrt(this.dot(this));
    }

    /**
     * Calculates the cosine similarity of this vector with another.
     *
     * @param other The other vector to compute cosine similarity with.
     * @return Cosine similarity between vectors
     */
    @Override
    public double cosineSimilarity(EmbeddingVector<TEmbedding> other) {
        if (this.size() != other.size()) {
            throw new IllegalArgumentException("Vectors lengths must be equal");
        }

        double dotProduct = this.dot(other);
        double normX = this.dot(this);
        double normY = other.dot(other);

        if (normX == 0 || normY == 0) {
            throw new IllegalArgumentException("Vectors cannot have zero norm");
        }

        return dotProduct / (Math.sqrt(normX) * Math.sqrt(normY));
    }

    @Override
    public EmbeddingVector<TEmbedding> multiply(double multiplier) {
        List<Double> result =
                this.getVector().stream()
                        .map(x -> x.doubleValue() * multiplier)
                        .collect(Collectors.toList());

        return (EmbeddingVector<TEmbedding>) new EmbeddingVector<>(result);
    }

    @Override
    public EmbeddingVector<TEmbedding> divide(double divisor) {
        if (Double.isNaN(divisor) || divisor == 0) {
            throw new IllegalArgumentException("Divisor cannot be zero");
        }

        List<Double> result =
                this.getVector().stream()
                        .map(x -> x.doubleValue() / divisor)
                        .collect(Collectors.toList());

        return (EmbeddingVector<TEmbedding>) new EmbeddingVector<>(result);
    }

    /**
     * Normalizes the underlying vector, such that the Euclidean length is 1.
     *
     * @return Normalized embedding
     */
    @Override
    public EmbeddingVector<TEmbedding> normalize() {
        return this.divide(this.euclideanLength());
    }
}
