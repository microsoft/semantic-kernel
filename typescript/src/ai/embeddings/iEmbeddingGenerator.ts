// Copyright (c) Microsoft. All rights reserved.

import { Verify } from '../../utils/verify';
import { Embedding } from './embedding';

/**
 * Represents a generator of embeddings.
 * @template TValue The type from which embeddings will be generated.
 */
interface IEmbeddingGenerator {
    /**
     * Generates an embedding from the given data.
     *
     * @param data List of strings to generate embeddings for
     * @returns List of embeddings
     */
    generateEmbeddings(data: string[]): Promise<Embedding[]>;
}

/**
 * Provides a collection of static methods for operating on IEmbeddingGenerator objects.
 */
export class EmbeddingGeneratorExtensions {
    /**
     * Generates an embedding from the given value.
     *
     * @template TValue The type from which embeddings will be generated.
     * @param generator The embedding generator.
     * @param value A value from which an Embedding will be generated.
     * @returns A list of {@link Embedding} structs representing the input value.
     */
    public static generateEmbedding(
        generator: IEmbeddingGenerator,
        value: string
    ): Promise<Embedding[]> {
        Verify.notNull(generator, 'Embeddings generator cannot be NULL');
        return generator.generateEmbeddings([value]);
    }
}
