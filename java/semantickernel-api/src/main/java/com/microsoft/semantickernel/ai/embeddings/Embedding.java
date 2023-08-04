// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.microsoft.semantickernel.ai.embeddings.VectorOperations;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import javax.annotation.Nonnull;

/** Represents a strongly typed vector of numeric data. */
public class Embedding {
  
  // vector is immutable!
  private final List<Float> vector;

  private static final Embedding EMPTY = new Embedding();

  public static Embedding empty() {
    return EMPTY;
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
  public Embedding(@Nonnull List<Float> vector) {
    Objects.requireNonNull(vector);
    this.vector = Collections.unmodifiableList(vector);
  }

  /**
   * Return the embedding vector as a read-only list.
   * @return The embedding vector as a read-only list.
   */
  public List<Float> getVector() {
    return vector;
  }

  /**
   * Calculates the dot product of this {@code Embedding} with another.
   *
   * @param other The other {@code Embedding} to compute the dot product with
   * @return The dot product between the {@code Embedding} vectors
   */
  public float dot(@Nonnull Embedding other) {
    Objects.requireNonNull(other);
    return VectorOperations.dot(this.vector, other.getVector());
  }

  /**
   * Calculates the Euclidean length of this vector.
   *
   * @return Euclidean length
   */
  public float euclideanLength() {
    return VectorOperations.euclideanLength(this.vector);
  }

  /**
   * Calculates the cosine similarity of this vector with another.
   *
   * @param other The other vector to compute cosine similarity with.
   * @return Cosine similarity between vectors
   */
  public float cosineSimilarity(@Nonnull Embedding other) {
    Objects.requireNonNull(other);
    return VectorOperations.cosineSimilarity(this.vector, other.getVector());
  }

  /**
   * Multiply the {@code Embedding} vector by a multiplier.
   * @param multiplier The multiplier to multiply the {@code Embedding} vector by
   * @return A new {@code Embedding} with the vector multiplied by the multiplier
   */
  public Embedding multiply(float multiplier) {
    return new Embedding(VectorOperations.multiply(this.vector, multiplier));
  }

  /**
   * Divide the {@code Embedding} vector by a divisor.
   * @param divisor The divisor to divide the {@code Embedding} vector by
   * @return A new {@code Embedding} with the vector divided by the divisor
   */
  public Embedding divide(float divisor) {
    return new Embedding(VectorOperations.divide(this.vector, divisor));
  }

  /**
   * Normalizes the underlying vector, such that the Euclidean length is 1.
   *
   * @return A new {@code Embedding} with the normalized vector
   */
  public Embedding normalize() {
    return new Embedding(VectorOperations.normalize(this.vector));
  }
}
